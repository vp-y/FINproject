from pydantic import BaseModel
from typing import Literal, Optional


class HoldingInput(BaseModel):

    input: str          # raw ticker OR free-text company name
    quantity: float
    purchase_price: float


class PortfolioProfileInput(BaseModel):

    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "moderate"
    investment_horizon: Literal["short", "medium", "long"] = "medium"
    investment_goal: Optional[str] = None


class CreatePortfolioRequest(BaseModel):

    user_name: str
    portfolio_name: str
    holdings: list[HoldingInput]
    profile: Optional[PortfolioProfileInput] = None


class HoldingResolution(BaseModel):

    input: str
    ticker: Optional[str]
    matched_name: Optional[str]
    confidence: float
    status: Literal["matched", "ambiguous", "not_found"]
    alternatives: list[dict] = []


class CreatedHolding(BaseModel):

    holding_id: int
    ticker: str
    matched_name: Optional[str]


class CreatePortfolioResponse(BaseModel):

    portfolio_id: int
    user_id: int
    created_holdings: list[CreatedHolding]
    needs_confirmation: list[HoldingResolution]


class ResolveTickerRequest(BaseModel):

    input: str
