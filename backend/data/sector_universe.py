# Free-tier-friendly "alternative investments" universe: a small,
# curated, liquid-large-cap candidate set per sector, used by
# analytics/recommendation_engine.py to suggest replacements for
# flagged holdings and to plug diversification gaps — no paid
# screener API involved. Sector keys are verified against real
# yfinance `Ticker(...).info.get("sector")` output (spot-checked
# against 20+ live tickers while building this), not guessed —
# yfinance's classification sometimes surprises (GOOGL/META/NFLX/DIS
# are "Communication Services", not "Technology"; AMZN/TSLA/HD are
# "Consumer Cyclical").
#
# This is a best-effort v1 list, not exhaustive — a reasonable
# candidate universe for a demo-scale platform, not a claim of
# completeness. Extend freely.

SECTOR_CANDIDATES: dict[str, list[str]] = {
    "Technology": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "ADBE", "CRM"],
    "Healthcare": ["JNJ", "UNH", "LLY", "PFE", "ABBV", "MRK", "TMO"],
    "Financial Services": ["JPM", "BAC", "WFC", "MA", "V", "GS", "BRK-B"],
    "Consumer Cyclical": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW"],
    "Consumer Defensive": ["KO", "PG", "WMT", "PEP", "COST", "PM", "CL"],
    "Industrials": ["HON", "UPS", "CAT", "GE", "LMT", "RTX", "UNP"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PSX", "OXY"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE"],
    "Real Estate": ["PLD", "AMT", "EQIX", "SPG", "PSA", "O", "WELL"],
    "Basic Materials": ["LIN", "SHW", "FCX", "ECL", "APD", "NEM", "NUE"],
    "Communication Services": ["GOOGL", "META", "VZ", "T", "DIS", "NFLX", "TMUS"],
}

SECTOR_ETFS: dict[str, str] = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Industrials": "XLI",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Basic Materials": "XLB",
    "Communication Services": "XLC",
}

# Broad-market passive benchmark used throughout the recommendation
# engine (beta/alpha/tracking error, benchmark Sharpe comparison).
BENCHMARK_TICKER = "SPY"

# Rough "fair value" trailing P/E band per sector, used only for a
# coarse over/undervalued/fair classification (analytics/fundamentals.py)
# — not a real valuation model, just a sanity-check heuristic against a
# sector-typical range instead of one fixed number for every company.
PE_RANGE_BY_SECTOR: dict[str, tuple[float, float]] = {
    "Technology": (20, 45),
    "Healthcare": (15, 30),
    "Financial Services": (8, 18),
    "Consumer Cyclical": (15, 35),
    "Consumer Defensive": (15, 28),
    "Industrials": (15, 28),
    "Energy": (8, 16),
    "Utilities": (14, 22),
    "Real Estate": (12, 25),
    "Basic Materials": (10, 20),
    "Communication Services": (12, 30),
}

DEFAULT_PE_RANGE: tuple[float, float] = (10, 30)
