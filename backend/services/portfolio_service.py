from datetime import datetime, timezone

from sqlalchemy.orm import Session
from database.models import Holding, Portfolio, PortfolioProfile, User, HoldingDocument


def get_holdings(
    db:Session,
    portfolio_id:int
):

    return db.query(
        Holding
    ).filter(
        Holding.portfolio_id == portfolio_id
    ).all()


def get_or_create_user(db: Session, name: str) -> User:

    user = db.query(User).filter(User.name == name).first()

    if user:
        return user

    user = User(name=name)
    db.add(user)
    db.flush()

    return user


def create_portfolio(db: Session, name: str, user_id: int) -> Portfolio:

    portfolio = Portfolio(name=name, user_id=user_id)
    db.add(portfolio)
    db.flush()

    return portfolio


def create_portfolio_profile(
    db: Session, portfolio_id: int, profile
) -> PortfolioProfile:

    row = PortfolioProfile(
        portfolio_id=portfolio_id,
        risk_tolerance=profile.risk_tolerance,
        investment_horizon=profile.investment_horizon,
        investment_goal=profile.investment_goal,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()

    return row


def create_holding(
    db: Session,
    portfolio_id: int,
    ticker: str,
    quantity: float,
    purchase_price: float,
) -> Holding:

    holding = Holding(
        portfolio_id=portfolio_id,
        ticker=ticker,
        quantity=quantity,
        purchase_price=purchase_price,
    )
    db.add(holding)
    db.flush()

    return holding


def get_portfolio(db: Session, portfolio_id: int) -> Portfolio | None:

    return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()


def get_portfolio_profile(db: Session, portfolio_id: int) -> PortfolioProfile | None:

    return (
        db.query(PortfolioProfile)
        .filter(PortfolioProfile.portfolio_id == portfolio_id)
        .order_by(PortfolioProfile.created_at.desc())
        .first()
    )


def list_portfolios(db: Session, user_id: int | None = None) -> list[Portfolio]:

    query = db.query(Portfolio)

    if user_id is not None:
        query = query.filter(Portfolio.user_id == user_id)

    return query.all()


def get_document_status_summary(db: Session, portfolio_id: int) -> dict:

    rows = (
        db.query(HoldingDocument)
        .filter(HoldingDocument.portfolio_id == portfolio_id)
        .all()
    )

    summary: dict[str, int] = {}

    for row in rows:
        summary[row.status] = summary.get(row.status, 0) + 1

    return summary
