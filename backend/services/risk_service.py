import yfinance as yf

from services.market_service import get_stock_price

CONCENTRATION_THRESHOLD = 0.5  # a single sector holding >=50% of the
                                # portfolio is flagged as high concentration

_sector_cache = {}


def get_sector(ticker):

    if ticker in _sector_cache:
        return _sector_cache[ticker]

    info = yf.Ticker(ticker).info
    sector = info.get("sector") or "Unknown"

    _sector_cache[ticker] = sector

    return sector


def analyze_portfolio_concentration(holdings):
    """
    holdings: Holding ORM rows (ticker, quantity, purchase_price).
    Uses real current market prices (not purchase price) to compute
    each position's live weight in the portfolio.
    """

    positions = []
    total_value = 0.0

    for holding in holdings:

        price_info = get_stock_price(holding.ticker)
        current_price = price_info["price"]
        value = current_price * holding.quantity

        total_value += value

        positions.append({
            "ticker": holding.ticker,
            "quantity": holding.quantity,
            "current_price": current_price,
            "value": value,
            "sector": get_sector(holding.ticker)
        })

    for position in positions:
        position["weight"] = (
            position["value"] / total_value if total_value else 0
        )

    positions.sort(key=lambda p: p["weight"], reverse=True)

    sector_weights = {}

    for position in positions:
        sector_weights[position["sector"]] = (
            sector_weights.get(position["sector"], 0) + position["weight"]
        )

    top_sector, top_sector_weight = max(
        sector_weights.items(),
        key=lambda kv: kv[1]
    )

    riskiest_companies = [
        p["ticker"] for p in positions if p["sector"] == top_sector
    ]

    return {
        "total_value": total_value,
        "positions": positions,
        "sector_weights": sector_weights,
        "top_sector": top_sector,
        "top_sector_weight": top_sector_weight,
        "concentration_flag": top_sector_weight >= CONCENTRATION_THRESHOLD,
        "riskiest_companies": riskiest_companies
    }
