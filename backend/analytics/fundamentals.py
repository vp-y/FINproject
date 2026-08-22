import yfinance as yf

from data.sector_universe import PE_RANGE_BY_SECTOR, DEFAULT_PE_RANGE

# Separate from services/risk_service.py's own _sector_cache — small
# enough duplication that it isn't worth coupling the two modules over.
# Same ticker is often looked up multiple times within one
# recommendation run (as a current holding, then again as a candidate
# alternative for a different flagged holding).
_fundamentals_cache: dict[str, dict] = {}


def get_fundamentals(ticker: str) -> dict:
    """Valuation/fundamentals snapshot pulled from yfinance's info
    payload: trailing/forward P/E, price-to-book, dividend yield, ROE,
    debt-to-equity, profit margins, revenue growth, market cap, sector."""

    if ticker in _fundamentals_cache:
        return _fundamentals_cache[ticker]

    info = yf.Ticker(ticker).info

    fundamentals = {
        "ticker": ticker,
        "sector": info.get("sector") or "Unknown",
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_book": info.get("priceToBook"),
        "dividend_yield": info.get("dividendYield"),
        "return_on_equity": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "profit_margins": info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "market_cap": info.get("marketCap"),
    }

    _fundamentals_cache[ticker] = fundamentals

    return fundamentals


def classify_valuation(ticker: str) -> str:
    """Coarse overvalued/undervalued/fair classification against a
    sector-typical trailing-P/E band (data/sector_universe.py) — not a
    real valuation model, just a directional signal for the
    recommendation engine's rules. "unknown" when trailing P/E isn't
    available (e.g. an unprofitable company)."""

    fundamentals = get_fundamentals(ticker)
    pe = fundamentals.get("trailing_pe")

    if pe is None or pe <= 0:
        return "unknown"

    low, high = PE_RANGE_BY_SECTOR.get(fundamentals["sector"], DEFAULT_PE_RANGE)

    if pe > high:
        return "overvalued"
    if pe < low:
        return "undervalued"
    return "fair"
