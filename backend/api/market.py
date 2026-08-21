from fastapi import APIRouter
from services.market_service import get_stock_price


router = APIRouter(
    prefix="/market",
    tags=["Market"]
)


@router.get("/{ticker}")
def price(ticker: str):

    return get_stock_price(
        ticker
    )
