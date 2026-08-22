from database.connection import SessionLocal
from services.portfolio_service import get_portfolio_profile
from services.market_service import get_historical_returns, get_stock_price
from data_pipeline.company_mapper import get_company_details
from data.sector_universe import SECTOR_CANDIDATES, SECTOR_ETFS

from analytics.risk_metrics import sharpe_ratio
from analytics.fundamentals import get_fundamentals, classify_valuation
from analytics.diversification import (
    calculate_herfindahl_index,
    effective_number_of_positions,
)
from analytics.correlation import average_pairwise_correlation
from analytics.benchmark import get_benchmark_returns, compare_to_benchmark
from analytics.drawdown import calculate_max_drawdown
from analytics.portfolio_metrics import compute_portfolio_metrics, strip_internal_fields
from tools.risk_tools import calculate_portfolio_risk

# All comparison/scoring math below is plain Python/pandas/yfinance data
# — no LLM call anywhere in this module. That's deliberate: Mistral's
# and Gemini's free-tier rate limits (see README) can't absorb an LLM
# call per candidate comparison. The one LLM call this whole feature
# needs (turning these structured verdicts into a narrative) happens
# once, downstream, in agent_orchestrator.run_recommendation_workflow.

DEFAULT_RISK_TOLERANCE = "moderate"
DEFAULT_INVESTMENT_HORIZON = "medium"

# Matches agent_orchestrator.py's extract_main_drivers threshold — a
# single holding at/above this weight is flagged as a concentration risk
# regardless of anything else about it.
SINGLE_HOLDING_THRESHOLD = 0.4

MAX_HEALTHY_WEIGHT = {
    "conservative": 0.15,
    "moderate": 0.20,
    "aggressive": 0.30,
}
DEFAULT_MAX_HEALTHY_WEIGHT = 0.20

MIN_EFFECTIVE_POSITIONS = 5
HIGH_CORRELATION_THRESHOLD = 0.7
DEEP_DRAWDOWN_THRESHOLD = -0.30
UNDERREPRESENTED_SECTOR_THRESHOLD = 0.05

ALTERNATIVES_PER_TICKER = 3
DIVERSIFICATION_SUGGESTIONS_LIMIT = 3
# Trailing trading days kept for each ticker's dashboard sparkline —
# enough to show a real shape, small enough to stay cheap in the payload.
SPARKLINE_POINTS = 30
# Each hypothetical add/increase is funded pro-rata from the rest of the
# portfolio, capped at 5 points (or 10% of whatever's being funded from,
# whichever is smaller) — a simple heuristic, not a mean-variance
# optimizer. Documented v1 scope; see compute_recommended_state.
MAX_HYPOTHETICAL_WEIGHT_SHIFT = 0.05
HYPOTHETICAL_WEIGHT_SHIFT_FRACTION = 0.10


def _load_profile(portfolio_id: int) -> dict:

    db = SessionLocal()
    try:
        profile_row = get_portfolio_profile(db, portfolio_id)
    finally:
        db.close()

    return {
        "risk_tolerance": profile_row.risk_tolerance if profile_row else DEFAULT_RISK_TOLERANCE,
        "investment_horizon": profile_row.investment_horizon if profile_row else DEFAULT_INVESTMENT_HORIZON,
    }


def identify_weaknesses(metrics: dict, profile: dict) -> list[dict]:
    """Rule-based weakness detection — one small, independently-testable
    check per rule, each appending a finding only when its condition
    actually triggers."""

    weaknesses = []

    def add(id_, category, severity, description, evidence):
        weaknesses.append({
            "id": id_,
            "category": category,
            "severity": severity,
            "description": description,
            "metric_evidence": evidence,
        })

    if metrics.get("concentration_flag"):
        severity = "high" if metrics["top_sector_weight"] >= 0.65 else "medium"
        add(
            "sector_concentration", "concentration", severity,
            f"{metrics['top_sector']} makes up {metrics['top_sector_weight'] * 100:.0f}% "
            f"of the portfolio — a downturn in that sector would hit the whole "
            f"portfolio disproportionately.",
            {"top_sector": metrics["top_sector"], "top_sector_weight": metrics["top_sector_weight"]},
        )

    for position in metrics.get("positions", []):
        if position["weight"] >= SINGLE_HOLDING_THRESHOLD:
            add(
                "single_holding_concentration", "concentration", "high",
                f"{position['ticker']} alone makes up "
                f"{position['weight'] * 100:.0f}% of the portfolio.",
                {"ticker": position["ticker"], "weight": position["weight"]},
            )

    effective_positions = metrics.get("effective_number_of_positions", 0)
    if effective_positions < MIN_EFFECTIVE_POSITIONS:
        add(
            "low_diversification", "diversification", "medium",
            f"The portfolio behaves like only about {effective_positions:.1f} "
            f"equally-weighted positions, even if it holds more tickers than that.",
            {"effective_number_of_positions": effective_positions},
        )

    average_correlation = metrics.get("average_pairwise_correlation", 0)
    if average_correlation > HIGH_CORRELATION_THRESHOLD:
        add(
            "high_correlation", "diversification", "medium",
            f"Holdings move together {average_correlation * 100:.0f}% of the time on "
            f"average — they don't diversify each other as much as their number suggests.",
            {"average_pairwise_correlation": average_correlation},
        )

    benchmark = metrics.get("benchmark") or {}
    benchmark_sharpe = benchmark.get("benchmark_sharpe_ratio")

    if benchmark_sharpe is not None and metrics.get("sharpe_ratio") is not None:
        if metrics["sharpe_ratio"] < benchmark_sharpe:
            add(
                "sub_benchmark_risk_adjusted_return", "performance", "medium",
                f"Risk-adjusted return (Sharpe {metrics['sharpe_ratio']:.2f}) trails the "
                f"S&P 500 benchmark (Sharpe {benchmark_sharpe:.2f}).",
                {"sharpe_ratio": metrics["sharpe_ratio"], "benchmark_sharpe_ratio": benchmark_sharpe},
            )

    max_drawdown = metrics.get("max_drawdown", 0)
    if max_drawdown < DEEP_DRAWDOWN_THRESHOLD:
        add(
            "deep_drawdown", "risk", "high",
            f"The portfolio has seen a peak-to-trough decline of "
            f"{max_drawdown * 100:.0f}% over the lookback window.",
            {"max_drawdown": max_drawdown},
        )

    overvalued = [
        p["ticker"] for p in metrics.get("positions", []) if p.get("valuation") == "overvalued"
    ]
    if overvalued:
        add(
            "overvalued_holdings", "valuation", "medium",
            f"{', '.join(overvalued)} {'is' if len(overvalued) == 1 else 'are'} trading "
            f"above a typical valuation range for their sector.",
            {"tickers": overvalued},
        )

    alpha = benchmark.get("alpha")
    if alpha is not None and alpha < 0:
        add(
            "negative_alpha", "performance", "medium",
            f"The portfolio has underperformed the S&P 500 on a risk-adjusted basis "
            f"(alpha {alpha * 100:+.1f}%/yr) over the lookback window.",
            {"alpha": alpha},
        )

    return weaknesses


def _score_ticker(ticker: str) -> dict:
    """Per-ticker scoring shared by current holdings and alternative
    candidates alike: its own risk-adjusted return (Sharpe on its own
    historical returns), valuation classification, and fundamentals.
    Carries the fetched return series under `_returns` (stripped before
    this data leaves the module) so a caller building a what-if
    portfolio doesn't need a second yfinance round-trip for it."""

    try:
        returns = get_historical_returns(ticker)
        risk_adjusted_return = float(sharpe_ratio(returns.values)) if len(returns) > 1 else 0.0
        # A compact trend series for the dashboard's sparklines — the
        # cumulative wealth index (starting at 1.0) over the last 30
        # trading days, from the same return series already fetched for
        # the Sharpe calculation above, so this costs no extra API call.
        sparkline = (1 + returns).cumprod().tail(SPARKLINE_POINTS).tolist()
        change_percent = (
            (sparkline[-1] / sparkline[0] - 1) * 100 if len(sparkline) > 1 else None
        )
    except Exception:
        returns = None
        risk_adjusted_return = 0.0
        sparkline = []
        change_percent = None

    try:
        # Only actually new for alternative candidates — score_holdings
        # already has each existing position's current_price from
        # analyze_portfolio_concentration and uses that instead, so this
        # doesn't double a call for tickers already held.
        current_price = get_stock_price(ticker)["price"]
    except Exception:
        current_price = None

    return {
        "ticker": ticker,
        "risk_adjusted_return": risk_adjusted_return,
        "valuation": classify_valuation(ticker),
        "fundamentals": get_fundamentals(ticker),
        "sparkline": sparkline,
        "change_percent": change_percent,
        "current_price": current_price,
        "_returns": returns,
    }


def classify_horizon(item: dict) -> str:
    """short_term | long_term for the dashboard's toggle. Deliberately a
    small rule, not a model: "sell" is treated as the one urgent,
    near-term action; rebalancing (reduce/increase/hold) is a gradual,
    long-term portfolio-management move."""

    return "short_term" if item.get("verdict") == "sell" else "long_term"


def score_holdings(metrics: dict, profile: dict) -> list[dict]:
    """Per-position hold/reduce/sell/increase verdict, from a plain
    decision tree over weight, risk contribution, risk-adjusted return,
    and valuation — no LLM judgment involved."""

    max_weight = MAX_HEALTHY_WEIGHT.get(profile.get("risk_tolerance"), DEFAULT_MAX_HEALTHY_WEIGHT)
    benchmark_sharpe = (metrics.get("benchmark") or {}).get("benchmark_sharpe_ratio")

    scored = []

    for position in metrics.get("positions", []):

        ticker = position["ticker"]
        weight = position["weight"]
        risk_contribution = position.get("risk_contribution", 0.0)
        risk_contribution_ratio = (risk_contribution / weight) if weight else 0.0

        score = _score_ticker(ticker)
        risk_adjusted_return = score["risk_adjusted_return"]
        valuation = score["valuation"]

        reasoning = []
        verdict = "hold"

        over_target_and_risky = weight > max_weight and risk_contribution_ratio > 1.3
        # Same threshold identify_weaknesses uses to flag a position as a
        # concentration risk in the first place — a weakness the dashboard
        # surfaces has to come with a matching action, or "hold, no strong
        # signal to change this position" would directly contradict the
        # weakness listed right next to it.
        over_single_holding_threshold = weight >= SINGLE_HOLDING_THRESHOLD

        if over_target_and_risky or over_single_holding_threshold:
            verdict = "reduce"
            if over_single_holding_threshold:
                reasoning.append(
                    f"Position is {weight * 100:.0f}% of the portfolio — at or above the "
                    f"{SINGLE_HOLDING_THRESHOLD * 100:.0f}% single-holding concentration threshold."
                )
            if over_target_and_risky:
                reasoning.append(
                    f"Above the {max_weight * 100:.0f}% target weight for a "
                    f"{profile.get('risk_tolerance', DEFAULT_RISK_TOLERANCE)} investor, and "
                    f"contributes disproportionately to risk ({risk_contribution_ratio:.1f}x its weight)."
                )
        elif risk_adjusted_return < 0 and weight > 0.02:
            verdict = "sell"
            reasoning.append(
                f"Negative risk-adjusted return (Sharpe {risk_adjusted_return:.2f}) "
                f"over the lookback window."
            )
        elif (
            valuation == "overvalued"
            and benchmark_sharpe is not None
            and risk_adjusted_return < benchmark_sharpe
        ):
            verdict = "reduce"
            reasoning.append(
                "Trading above a typical valuation range for its sector, and "
                "underperforming the benchmark on a risk-adjusted basis."
            )
        elif (
            valuation == "undervalued"
            and benchmark_sharpe is not None
            and risk_adjusted_return > benchmark_sharpe
            and weight < max_weight
        ):
            verdict = "increase"
            reasoning.append(
                f"Trading below a typical valuation range for its sector, with "
                f"risk-adjusted return above the benchmark, and still under the "
                f"{max_weight * 100:.0f}% target weight."
            )
        else:
            reasoning.append("No strong signal to change this position.")

        holding_action = {
            "ticker": ticker,
            "verdict": verdict,
            "weight": weight,
            "risk_contribution": risk_contribution,
            "risk_contribution_ratio": risk_contribution_ratio,
            "risk_adjusted_return": risk_adjusted_return,
            "valuation": valuation,
            "sector": position.get("sector"),
            "reasoning": reasoning,
            # Real weighted-average price from the position itself (not
            # score["current_price"], which would be a redundant fetch
            # for a ticker we already have the live price for).
            "current_price": position.get("current_price"),
            "change_percent": score.get("change_percent"),
            "sparkline": score.get("sparkline", []),
        }
        holding_action["horizon"] = classify_horizon(holding_action)
        holding_action["expected_impact"] = estimate_single_action_impact(holding_action, metrics)

        scored.append(holding_action)

    return scored


def _build_alternative_rationale(holding: dict, candidate_score: dict, sector: str) -> list[str]:

    action_word = "sell" if holding["verdict"] == "sell" else "reduce"

    reasons = [
        f"Same sector ({sector}) as {holding['ticker']}, which is flagged to {action_word}."
    ]

    if candidate_score["valuation"] == "undervalued":
        reasons.append("Trading below a typical valuation range for its sector.")

    if candidate_score["risk_adjusted_return"] > holding["risk_adjusted_return"]:
        reasons.append(
            f"Stronger risk-adjusted return ({candidate_score['risk_adjusted_return']:.2f} Sharpe) "
            f"than {holding['ticker']} ({holding['risk_adjusted_return']:.2f})."
        )

    return reasons


def find_alternatives(holding_scores: list[dict], metrics: dict, profile: dict) -> list[dict]:
    """For each reduce/sell holding, candidates from that sector's
    curated universe (data/sector_universe.py) plus its sector ETF,
    scored the same way as any holding, ranked by risk-adjusted return.
    No paid screener API — a small, free, bounded candidate set."""

    held_tickers = {p["ticker"] for p in metrics.get("positions", [])}
    alternatives = []

    for holding in holding_scores:

        if holding["verdict"] not in ("reduce", "sell"):
            continue

        sector = holding.get("sector") or "Unknown"
        candidates = list(SECTOR_CANDIDATES.get(sector, []))

        etf = SECTOR_ETFS.get(sector)
        if etf:
            candidates.append(etf)

        candidates = [
            candidate for candidate in candidates
            if candidate not in held_tickers and candidate != holding["ticker"]
        ]

        scored_candidates = []

        for candidate in candidates:

            score = _score_ticker(candidate)
            company_name = get_company_details(candidate).get("name") or candidate

            scored_candidates.append({
                "replaces_ticker": holding["ticker"],
                "candidate_ticker": candidate,
                "candidate_name": company_name,
                "sector": sector,
                "risk_adjusted_return": score["risk_adjusted_return"],
                "valuation": score["valuation"],
                "rationale": _build_alternative_rationale(holding, score, sector),
                "horizon": classify_horizon(holding),
                "current_price": score.get("current_price"),
                "change_percent": score.get("change_percent"),
                "sparkline": score.get("sparkline", []),
                "_returns": score["_returns"],
            })

        scored_candidates.sort(key=lambda c: c["risk_adjusted_return"], reverse=True)
        alternatives.extend(scored_candidates[:ALTERNATIVES_PER_TICKER])

    return alternatives


def build_diversification_recommendations(metrics: dict, profile: dict) -> list[dict]:
    """Suggests sector ETFs for sectors the portfolio has little or no
    exposure to — independent of any individual holding being flagged,
    since a portfolio can be well-performing but narrowly diversified."""

    sector_weights = metrics.get("sector_weights", {})
    held_tickers = {p["ticker"] for p in metrics.get("positions", [])}

    # Already reasonably spread across sectors — don't manufacture
    # suggestions where there isn't a real gap.
    if not metrics.get("concentration_flag") and len(sector_weights) >= 4:
        return []

    underrepresented = [
        sector for sector in SECTOR_CANDIDATES
        if sector_weights.get(sector, 0.0) < UNDERREPRESENTED_SECTOR_THRESHOLD
    ]

    suggestions = []

    for sector in underrepresented[:DIVERSIFICATION_SUGGESTIONS_LIMIT]:

        etf = SECTOR_ETFS.get(sector)

        if not etf or etf in held_tickers:
            continue

        score = _score_ticker(etf)

        suggestions.append({
            "replaces_ticker": None,
            "candidate_ticker": etf,
            "candidate_name": f"{sector} Sector ETF",
            "sector": sector,
            "rationale": [
                f"The portfolio currently has little to no exposure to {sector} "
                f"({sector_weights.get(sector, 0.0) * 100:.0f}%) — a broad, low-cost "
                f"way to add it without picking a single company."
            ],
            "horizon": "long_term",
            "current_price": score.get("current_price"),
            "change_percent": score.get("change_percent"),
            "sparkline": score.get("sparkline", []),
        })

    return suggestions


def _distribute_pro_rata(weights: dict, amount: float, exclude: str = None):
    """Spreads `amount` across all remaining weights, proportional to
    their current size (used when freeing up weight from a sell/reduce)."""

    total = sum(w for t, w in weights.items() if t != exclude)

    if not total:
        return

    for ticker in list(weights.keys()):
        if ticker == exclude:
            continue
        weights[ticker] += amount * (weights[ticker] / total)


def _take_pro_rata(weights: dict, amount: float, exclude: str = None):
    """Trims `amount` off all remaining weights, proportional to their
    current size, to fund an increase/add elsewhere."""

    total = sum(w for t, w in weights.items() if t != exclude)

    if not total:
        return

    for ticker in list(weights.keys()):
        if ticker == exclude:
            continue
        weights[ticker] -= amount * (weights[ticker] / total)


def _reweight_existing(weights: dict, ticker: str, verdict: str) -> dict:
    """Applies one hypothetical action to an EXISTING position's weight,
    redistributing pro-rata across the rest. A simple heuristic, not a
    mean-variance optimizer — documented v1 scope."""

    if ticker not in weights:
        return dict(weights)

    new_weights = dict(weights)

    if verdict == "sell":
        removed = new_weights.pop(ticker)
        _distribute_pro_rata(new_weights, removed)

    elif verdict == "reduce":
        cut = new_weights[ticker] * 0.5
        new_weights[ticker] -= cut
        _distribute_pro_rata(new_weights, cut, exclude=ticker)

    elif verdict == "increase":
        bump = min(
            MAX_HYPOTHETICAL_WEIGHT_SHIFT,
            sum(w for t, w in new_weights.items() if t != ticker) * HYPOTHETICAL_WEIGHT_SHIFT_FRACTION,
        )
        _take_pro_rata(new_weights, bump, exclude=ticker)
        new_weights[ticker] += bump

    return new_weights


def estimate_single_action_impact(action: dict, metrics: dict) -> dict:
    """What-if: recompute volatility/Sharpe/VaR/HHI/top-sector-weight
    after applying ONLY this one holding_action, using the already-
    cached returns_df (no new network calls).

    Scoped to existing positions (sell/reduce/increase/hold on a
    currently-held ticker) — alternatives/diversification suggestions
    don't get a per-item estimate here, since they involve a ticker with
    no existing weight to perturb in isolation; their aggregate effect
    is captured instead by compute_recommended_state's full recompute,
    which does have their real historical returns on hand (fetched
    while scoring them)."""

    empty = {
        "volatility_delta": None,
        "sharpe_delta": None,
        "var_delta": None,
        "hhi_delta": None,
        "top_sector_weight_delta": None,
    }

    returns_df = metrics.get("_returns_df")
    current_weights = metrics.get("weights", {})
    ticker = action.get("ticker")

    if returns_df is None or ticker not in current_weights:
        return empty

    new_weights = _reweight_existing(current_weights, ticker, action.get("verdict"))

    tickers = [t for t in new_weights if t in returns_df.columns and new_weights[t] > 0]

    if not tickers:
        return empty

    hypothetical_returns = sum(returns_df[t] * new_weights[t] for t in tickers)

    new_risk = calculate_portfolio_risk(list(hypothetical_returns))
    new_hhi = calculate_herfindahl_index({t: new_weights[t] for t in tickers})

    sector_by_ticker = {p["ticker"]: p.get("sector") for p in metrics.get("positions", [])}
    new_sector_weights: dict[str, float] = {}
    for t in tickers:
        sector = sector_by_ticker.get(t) or "Unknown"
        new_sector_weights[sector] = new_sector_weights.get(sector, 0.0) + new_weights[t]
    new_top_sector_weight = max(new_sector_weights.values()) if new_sector_weights else 0.0

    return {
        "volatility_delta": new_risk["annualized_volatility"] - metrics["volatility"],
        "sharpe_delta": new_risk["sharpe_ratio"] - metrics["sharpe_ratio"],
        "var_delta": new_risk["historical_var_95"] - metrics["var_95"],
        "hhi_delta": new_hhi - metrics["herfindahl_index"],
        "top_sector_weight_delta": new_top_sector_weight - metrics["top_sector_weight"],
    }


def compute_recommended_state(
    metrics: dict, holding_scores: list[dict], alternatives: list[dict]
) -> dict:
    """Applies every recommended action together (every sell/reduce/
    increase verdict, plus every alternative addition) and recomputes
    the full metrics bundle on the resulting hypothetical portfolio — a
    genuine recompute, not an approximation, since each alternative's
    real historical return series was already fetched while scoring it
    (find_alternatives -> _score_ticker)."""

    returns_df = metrics.get("_returns_df")

    if returns_df is None:
        return {}

    weights = dict(metrics.get("weights", {}))
    working_df = returns_df.copy()

    for holding in holding_scores:
        weights = _reweight_existing(weights, holding["ticker"], holding["verdict"])

    for alternative in alternatives:

        candidate_returns = alternative.get("_returns")
        if candidate_returns is None:
            continue

        ticker = alternative["candidate_ticker"]

        if ticker not in working_df.columns:
            working_df[ticker] = candidate_returns.reindex(working_df.index).fillna(0)

        add_weight = min(
            MAX_HYPOTHETICAL_WEIGHT_SHIFT,
            sum(weights.values()) * HYPOTHETICAL_WEIGHT_SHIFT_FRACTION,
        )
        _take_pro_rata(weights, add_weight, exclude=ticker)
        weights[ticker] = weights.get(ticker, 0.0) + add_weight

    tickers = [t for t in weights if t in working_df.columns and weights[t] > 0]

    if not tickers:
        return {}

    hypothetical_returns = sum(working_df[t] * weights[t] for t in tickers)

    new_risk = calculate_portfolio_risk(list(hypothetical_returns))
    new_hhi = calculate_herfindahl_index({t: weights[t] for t in tickers})
    new_effective_positions = effective_number_of_positions(new_hhi)

    new_avg_correlation = (
        average_pairwise_correlation(working_df[tickers]) if len(tickers) > 1 else 0.0
    )

    sector_by_ticker = {p["ticker"]: p.get("sector") for p in metrics.get("positions", [])}
    for alternative in alternatives:
        sector_by_ticker.setdefault(alternative["candidate_ticker"], alternative.get("sector"))

    new_sector_weights: dict[str, float] = {}
    for t in tickers:
        sector = sector_by_ticker.get(t) or "Unknown"
        new_sector_weights[sector] = new_sector_weights.get(sector, 0.0) + weights[t]

    top_sector, top_sector_weight = (
        max(new_sector_weights.items(), key=lambda kv: kv[1])
        if new_sector_weights else (None, 0.0)
    )

    try:
        benchmark_returns = get_benchmark_returns()
        benchmark = compare_to_benchmark(hypothetical_returns, benchmark_returns)
    except Exception:
        benchmark = metrics.get("benchmark")

    drawdown = calculate_max_drawdown(hypothetical_returns)

    return {
        "volatility": new_risk["annualized_volatility"],
        "sharpe_ratio": new_risk["sharpe_ratio"],
        "var_95": new_risk["historical_var_95"],
        "weights": {t: weights[t] for t in tickers},
        "sector_weights": new_sector_weights,
        "top_sector": top_sector,
        "top_sector_weight": top_sector_weight,
        "herfindahl_index": new_hhi,
        "effective_number_of_positions": new_effective_positions,
        "average_pairwise_correlation": new_avg_correlation,
        "benchmark": benchmark,
        "max_drawdown": drawdown["max_drawdown"],
    }


_METRICS_COMPARISON_SPEC = [
    # (key, label, invert) — invert=True means a LOWER value is better
    # (e.g. volatility), matching frontend/src/lib/format.ts's
    # deltaTone(value, invert) convention exactly, so the frontend never
    # has to re-derive which direction is "good" per metric.
    ("volatility", "Volatility", True),
    ("sharpe_ratio", "Sharpe Ratio", False),
    ("var_95", "Value at Risk (95%)", False),
    ("herfindahl_index", "Concentration (HHI)", True),
    ("effective_number_of_positions", "Effective # of Positions", False),
    ("average_pairwise_correlation", "Avg. Correlation", True),
    ("top_sector_weight", "Top Sector Weight", True),
    ("max_drawdown", "Max Drawdown", False),
]


def _build_metrics_comparison(current: dict, recommended: dict) -> list[dict]:

    comparison = []

    for key, label, invert in _METRICS_COMPARISON_SPEC:

        current_value = current.get(key)
        recommended_value = recommended.get(key) if recommended else None

        if current_value is None or recommended_value is None:
            continue

        comparison.append({
            "metric": key,
            "label": label,
            "current": current_value,
            "recommended": recommended_value,
            "delta": recommended_value - current_value,
            "invert": invert,
        })

    return comparison


def generate_recommendation(portfolio_id: int, profile: dict = None) -> dict:
    """Single entry point: quant metrics -> weaknesses -> per-holding
    verdicts -> alternatives -> diversification gaps -> recommended
    portfolio state -> metrics comparison. No LLM call in this function
    or anything it calls — agent_orchestrator.run_recommendation_workflow
    is where the one narrative-generation LLM call happens, over this
    function's output."""

    if profile is None:
        profile = _load_profile(portfolio_id)

    metrics = compute_portfolio_metrics(portfolio_id)

    if "error" in metrics:
        return metrics

    weaknesses = identify_weaknesses(metrics, profile)
    holding_scores = score_holdings(metrics, profile)
    alternatives = find_alternatives(holding_scores, metrics, profile)
    diversification_suggestions = build_diversification_recommendations(metrics, profile)

    recommended_metrics = compute_recommended_state(metrics, holding_scores, alternatives)
    current_metrics = strip_internal_fields(metrics)

    metrics_comparison = _build_metrics_comparison(current_metrics, recommended_metrics)

    clean_alternatives = [
        {key: value for key, value in alternative.items() if not key.startswith("_")}
        for alternative in alternatives
    ]

    return {
        "portfolio_id": portfolio_id,
        "current_metrics": current_metrics,
        "recommended_metrics": recommended_metrics,
        "metrics_comparison": metrics_comparison,
        "weaknesses": weaknesses,
        "holding_actions": holding_scores,
        "alternatives": clean_alternatives,
        "diversification_suggestions": diversification_suggestions,
    }
