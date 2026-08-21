from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from services.portfolio_service import get_holdings


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)


@router.get("/{portfolio_id}/holdings")
def holdings(
    portfolio_id:int,
    db:Session=Depends(get_db)
):

    data = get_holdings(
        db,
        portfolio_id
    )

    return data