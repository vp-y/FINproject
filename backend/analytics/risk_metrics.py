import numpy as np


def calculate_volatility(
    returns
):

    return np.std(
        returns
    ) * np.sqrt(252)


def sharpe_ratio(
    returns,
    risk_free=0.05
):

    annual_return = (
        np.mean(returns)
        * 252
    )

    volatility = (
        np.std(returns)
        * np.sqrt(252)
    )

    return (
        annual_return - risk_free
    ) / volatility


def historical_var(
    returns,
    confidence=0.95
):

    return np.percentile(
        returns,
        (1 - confidence) * 100
    )
