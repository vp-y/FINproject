import numpy as np


def calculate_risk_contribution(
    weights: np.ndarray,
    covariance_matrix: np.ndarray,
) -> np.ndarray:

    portfolio_variance = (
        weights.T
        @ covariance_matrix
        @ weights
    )

    marginal_contribution = (
        covariance_matrix
        @ weights
    )

    contribution = (
        weights
        * marginal_contribution
        / portfolio_variance
    )

    return contribution
