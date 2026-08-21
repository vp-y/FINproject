from fastapi import APIRouter
import numpy as np

from analytics.risk_metrics import (
    calculate_volatility,
    sharpe_ratio,
    historical_var
)
from services.insight_service import explain_portfolio_risk


router = APIRouter(
    prefix="/risk",
    tags=["Risk"]
)


@router.post("/calculate")
def calculate():

    returns = np.random.normal(
        0.001,
        0.02,
        252
    )

    return {

        "volatility":
        calculate_volatility(
            returns
        ),

        "sharpe":
        sharpe_ratio(
            returns
        ),

        "VaR":
        historical_var(
            returns
        )
    }


@router.get("/{portfolio_id}/explain")
def explain(
    portfolio_id: int
):

    return explain_portfolio_risk(
        portfolio_id
    )
