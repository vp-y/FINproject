from sqlalchemy.orm import Session
from database.connection import SessionLocal
from services.portfolio_service import get_holdings


def get_portfolio_holdings(portfolio_id: int) -> dict:
    """
    Retrieve all holdings for a portfolio.

    Use this tool when the user asks about portfolio composition,
    holdings, tickers, quantities, or asset allocation.

    Args:
        portfolio_id: Portfolio identifier.

    Returns:
        Portfolio holdings.
    """

    db: Session = SessionLocal()

    try:
        holdings = get_holdings(db, portfolio_id)

        return {
            "portfolio_id": portfolio_id,
            "holdings": [
                {
                    "ticker": holding.ticker,
                    "quantity": holding.quantity,
                    "purchase_price": holding.purchase_price,
                }
                for holding in holdings
            ],
        }

    finally:
        db.close()
