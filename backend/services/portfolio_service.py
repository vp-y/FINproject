from sqlalchemy.orm import Session
from database.models import Holding


def get_holdings(
    db:Session,
    portfolio_id:int
):

    return db.query(
        Holding
    ).filter(
        Holding.portfolio_id == portfolio_id
    ).all()