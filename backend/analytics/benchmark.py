import numpy as np
import pandas as pd

from services.market_service import get_historical_returns
from analytics.risk_metrics import sharpe_ratio
from data.sector_universe import BENCHMARK_TICKER


def get_benchmark_returns(ticker: str = BENCHMARK_TICKER, period: str = "1y"):
    """Same shape as services.market_service.get_historical_returns — a
    pandas Series of daily returns — just aliased under a benchmark-
    specific name for readability at call sites."""

    return get_historical_returns(ticker, period)


def compare_to_benchmark(portfolio_returns, benchmark_returns) -> dict:
    """Aligns the portfolio's and benchmark's daily return series on a
    common date index, then computes beta/alpha/tracking error and each
    side's own annualized return + Sharpe.

    Returns None for every field if there isn't enough overlapping data
    to compute anything meaningful (e.g. a brand-new portfolio) — never
    a divide-by-zero or a misleading zero."""

    aligned = pd.concat(
        [
            pd.Series(portfolio_returns, name="portfolio"),
            pd.Series(benchmark_returns, name="benchmark"),
        ],
        axis=1,
        join="inner",
    ).dropna()

    if len(aligned) < 2:
        return {
            "beta": None,
            "alpha": None,
            "tracking_error": None,
            "benchmark_sharpe_ratio": None,
            "portfolio_annual_return": None,
            "benchmark_annual_return": None,
        }

    portfolio = aligned["portfolio"]
    benchmark = aligned["benchmark"]

    benchmark_variance = np.var(benchmark)
    covariance = np.cov(portfolio, benchmark)[0][1]

    beta = float(covariance / benchmark_variance) if benchmark_variance else None

    portfolio_annual_return = float(portfolio.mean() * 252)
    benchmark_annual_return = float(benchmark.mean() * 252)

    alpha = (
        portfolio_annual_return - beta * benchmark_annual_return
        if beta is not None else None
    )

    tracking_error = float((portfolio - benchmark).std() * np.sqrt(252))

    return {
        "beta": beta,
        "alpha": alpha,
        "tracking_error": tracking_error,
        "benchmark_sharpe_ratio": float(sharpe_ratio(benchmark.values)),
        "portfolio_annual_return": portfolio_annual_return,
        "benchmark_annual_return": benchmark_annual_return,
    }
