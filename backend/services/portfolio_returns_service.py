import pandas as pd

from database.connection import SessionLocal
from services.portfolio_service import get_holdings
from services.market_service import get_stock_price, get_historical_returns


def get_portfolio_returns_series(portfolio_id: int) -> dict:
    """
    Shared building block for anything that needs a portfolio's
    value-weighted historical return series. Used by risk_tools.py's two
    ADK tools (analyze_portfolio_risk, analyze_risk_contribution) and by
    the recommendation engine (analytics/portfolio_metrics.py) — single
    source of truth for "holdings -> live prices -> weights -> aligned
    historical returns" so that pipeline isn't duplicated across callers.

    Returns {"weights", "returns_df", "portfolio_returns", "total_value"}
    or {"error": "..."} if the portfolio has no holdings.
    """

    db = SessionLocal()

    try:
        holdings = get_holdings(db, portfolio_id)

        if not holdings:
            return {"error": f"No holdings found for portfolio {portfolio_id}."}

        weights = {}
        returns_by_ticker = {}
        total_value = 0.0

        for holding in holdings:

            price_info = get_stock_price(holding.ticker)
            value = price_info["price"] * holding.quantity

            total_value += value
            weights[holding.ticker] = value
            returns_by_ticker[holding.ticker] = get_historical_returns(holding.ticker)

        for ticker in weights:
            weights[ticker] = (
                weights[ticker] / total_value if total_value else 0
            )

        # Align all tickers' return series onto a common date index
        # (some tickers may be missing data on days others have it).
        returns_df = pd.DataFrame(returns_by_ticker).fillna(0)

        portfolio_returns = sum(
            returns_df[ticker] * weight
            for ticker, weight in weights.items()
        )

        return {
            "weights": weights,
            "returns_df": returns_df,
            "portfolio_returns": portfolio_returns,
            "total_value": total_value,
        }

    finally:
        db.close()
