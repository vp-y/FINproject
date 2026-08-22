from database.connection import SessionLocal
from services.portfolio_service import get_holdings
from services.portfolio_returns_service import get_portfolio_returns_series
from services.risk_service import analyze_portfolio_concentration
from tools.risk_tools import analyze_portfolio_risk, analyze_risk_contribution

from analytics.diversification import (
    calculate_herfindahl_index,
    effective_number_of_positions,
)
from analytics.correlation import (
    calculate_correlation_matrix,
    average_pairwise_correlation,
)
from analytics.benchmark import get_benchmark_returns, compare_to_benchmark
from analytics.drawdown import calculate_max_drawdown
from analytics.fundamentals import get_fundamentals, classify_valuation


def compute_portfolio_metrics(portfolio_id: int) -> dict:
    """The full "current state" bundle the recommendation engine builds
    everything else from: returns, risk, concentration, diversification,
    correlation, benchmark comparison, drawdown, and per-position
    fundamentals/valuation — one comprehensive pass, reusing the
    existing risk/concentration tools rather than recomputing what they
    already do.

    Returns {"error": "..."} if the portfolio has no holdings. On
    success, also carries two internal-only keys (`_returns_df`,
    `_portfolio_returns` — pandas objects) so
    analytics/recommendation_engine.py's what-if impact estimation and
    recommended-state recompute can reuse them without a second yfinance
    round-trip. strip_internal_fields() removes them before anything
    crosses an API boundary — call it before returning this dict (or
    anything derived from it) from an endpoint.
    """

    db = SessionLocal()
    try:
        holdings = get_holdings(db, portfolio_id)
    finally:
        db.close()

    if not holdings:
        return {"error": f"No holdings found for portfolio {portfolio_id}."}

    returns_series = get_portfolio_returns_series(portfolio_id)

    if "error" in returns_series:
        return returns_series

    returns_df = returns_series["returns_df"]
    portfolio_returns = returns_series["portfolio_returns"]
    weights = returns_series["weights"]

    risk = analyze_portfolio_risk(portfolio_id)

    if "error" in risk:
        return risk

    contribution_result = analyze_risk_contribution(portfolio_id)
    contribution = contribution_result.get("contribution", {})

    concentration = analyze_portfolio_concentration(holdings)

    hhi = calculate_herfindahl_index(weights)
    effective_positions = effective_number_of_positions(hhi)

    average_correlation = average_pairwise_correlation(returns_df)
    correlation_matrix = calculate_correlation_matrix(returns_df)

    # A yfinance hiccup fetching the benchmark shouldn't sink the whole
    # analysis — degrade to an all-None benchmark block instead.
    try:
        benchmark_returns = get_benchmark_returns()
        benchmark = compare_to_benchmark(portfolio_returns, benchmark_returns)
    except Exception:
        benchmark = {
            "beta": None,
            "alpha": None,
            "tracking_error": None,
            "benchmark_sharpe_ratio": None,
            "portfolio_annual_return": None,
            "benchmark_annual_return": None,
        }

    drawdown = calculate_max_drawdown(portfolio_returns)

    positions = []

    for position in concentration["positions"]:

        ticker = position["ticker"]

        positions.append({
            **position,
            "risk_contribution": contribution.get(ticker, 0.0),
            "valuation": classify_valuation(ticker),
            "fundamentals": get_fundamentals(ticker),
        })

    return {
        "portfolio_id": portfolio_id,
        "volatility": risk["annualized_volatility"],
        "sharpe_ratio": risk["sharpe_ratio"],
        "var_95": risk["historical_var_95"],
        "weights": weights,
        "total_value": concentration["total_value"],
        "positions": positions,
        "sector_weights": concentration["sector_weights"],
        "top_sector": concentration["top_sector"],
        "top_sector_weight": concentration["top_sector_weight"],
        "concentration_flag": concentration["concentration_flag"],
        "herfindahl_index": hhi,
        "effective_number_of_positions": effective_positions,
        "average_pairwise_correlation": average_correlation,
        "correlation_matrix": correlation_matrix,
        "benchmark": benchmark,
        "max_drawdown": drawdown["max_drawdown"],
        "max_drawdown_trough_date": drawdown["trough_date"],
        "_returns_df": returns_df,
        "_portfolio_returns": portfolio_returns,
    }


def strip_internal_fields(metrics: dict) -> dict:
    """Removes the pandas-object-carrying internal keys (prefixed `_`)
    before a metrics dict crosses an API boundary — JSON serialization
    would choke on them anyway."""

    return {key: value for key, value in metrics.items() if not key.startswith("_")}
