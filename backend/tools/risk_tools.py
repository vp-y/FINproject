import numpy as np
import pandas as pd
from analytics.risk_metrics import (
    calculate_volatility,
    sharpe_ratio,
    historical_var,
)
from database.connection import SessionLocal
from services.portfolio_service import get_holdings
from services.market_service import get_stock_price, get_historical_returns
from analytics.risk_contribution import calculate_risk_contribution


def calculate_portfolio_risk(
    returns: list[float],
) -> dict:
    """
    Calculate deterministic portfolio risk metrics.

    Use this tool when the user asks about volatility,
    Value at Risk, Sharpe ratio, or portfolio risk.

    Args:
        returns: Historical portfolio returns.

    Returns:
        Risk metrics calculated by the analytics engine.
    """

    returns_array = np.array(returns)

    volatility = calculate_volatility(returns_array)
    sharpe = sharpe_ratio(returns_array)
    var = historical_var(returns_array)

    return {
        "annualized_volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
        "historical_var_95": float(var),
    }


def analyze_portfolio_risk(
    portfolio_id: int,
) -> dict:
    """
    Perform end-to-end deterministic risk analysis for a portfolio.

    Retrieves holdings and real historical market prices, calculates
    value-weighted portfolio returns, and computes risk metrics from
    them. Prefer this tool over calculate_portfolio_risk when the user
    gives a portfolio rather than raw returns — it does the whole
    pipeline (Holdings -> Historical Prices -> Returns -> Risk Engine)
    instead of requiring the caller to already have a returns series.

    Args:
        portfolio_id: Portfolio identifier.

    Returns:
        Risk metrics, along with each holding's portfolio weight.
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

        result = calculate_portfolio_risk(
            list(portfolio_returns)
        )

        result["portfolio_id"] = portfolio_id
        result["weights"] = weights

        return result

    finally:
        db.close()


def analyze_risk_contribution(
    portfolio_id: int,
) -> dict:
    """
    Break down which holdings contribute most to portfolio risk, using
    a real covariance matrix built from historical returns — not just
    position weight. A smaller but highly volatile, highly correlated
    holding can dominate portfolio risk far more than its weight alone
    would suggest.

    Args:
        portfolio_id: Portfolio identifier.

    Returns:
        Each ticker's share of total portfolio risk (sums to ~1.0).
    """

    db = SessionLocal()

    try:
        holdings = get_holdings(db, portfolio_id)

        if not holdings:
            return {"error": f"No holdings found for portfolio {portfolio_id}."}

        tickers = [h.ticker for h in holdings]

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

        returns_df = pd.DataFrame(returns_by_ticker).fillna(0)

        weights_array = np.array([weights[t] for t in tickers])
        # annualized covariance, matching calculate_volatility's *sqrt(252)
        covariance_matrix = returns_df[tickers].cov().values * 252

        contribution = calculate_risk_contribution(
            weights_array,
            covariance_matrix
        )

        total_contribution = contribution.sum()

        contribution_pct = {
            ticker: float(value / total_contribution) if total_contribution else 0.0
            for ticker, value in zip(tickers, contribution)
        }

        return {
            "portfolio_id": portfolio_id,
            "contribution": contribution_pct,
        }

    finally:
        db.close()
