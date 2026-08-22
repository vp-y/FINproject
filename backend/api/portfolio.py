from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import PortfolioRecommendation
from services.portfolio_service import (
    get_holdings,
    get_or_create_user,
    create_portfolio,
    create_portfolio_profile,
    create_holding,
    get_portfolio,
    get_portfolio_profile,
    list_portfolios,
    get_document_status_summary,
)
from services.ticker_resolver import resolve_ticker, resolve_holdings_input
from schemas.portfolio import (
    CreatePortfolioRequest,
    CreatePortfolioResponse,
    CreatedHolding,
    HoldingInput,
    HoldingResolution,
    ResolveTickerRequest,
)


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)


def _resolve_and_write_holdings(
    db: Session, portfolio_id: int, holdings: list[HoldingInput]
) -> tuple[list[CreatedHolding], list[HoldingResolution]]:
    """Shared by POST /portfolio and POST /portfolio/{id}/holdings: only
    rows that resolve to a real ticker with confidence are written —
    ambiguous/not_found rows come back for the caller to confirm/retype,
    never silently written as a guess."""

    resolved_rows = resolve_holdings_input(
        [
            {
                "input": h.input,
                "quantity": h.quantity,
                "purchase_price": h.purchase_price,
            }
            for h in holdings
        ]
    )

    created_holdings = []
    needs_confirmation = []

    for row in resolved_rows:

        resolution = row["resolution"]

        if resolution["status"] == "matched":

            holding = create_holding(
                db,
                portfolio_id,
                resolution["ticker"],
                row["quantity"],
                row["purchase_price"],
            )

            created_holdings.append(CreatedHolding(
                holding_id=holding.id,
                ticker=holding.ticker,
                matched_name=resolution["matched_name"],
            ))

        else:

            needs_confirmation.append(HoldingResolution(**resolution))

    return created_holdings, needs_confirmation


@router.post("", response_model=CreatePortfolioResponse)
def create_portfolio_endpoint(
    request: CreatePortfolioRequest,
    db: Session = Depends(get_db),
):

    user = get_or_create_user(db, request.user_name)
    portfolio = create_portfolio(db, request.portfolio_name, user.id)

    if request.profile:
        create_portfolio_profile(db, portfolio.id, request.profile)

    created_holdings, needs_confirmation = _resolve_and_write_holdings(
        db, portfolio.id, request.holdings
    )

    db.commit()

    return CreatePortfolioResponse(
        portfolio_id=portfolio.id,
        user_id=user.id,
        created_holdings=created_holdings,
        needs_confirmation=needs_confirmation,
    )


@router.get("")
def list_portfolios_endpoint(
    user_id: int | None = None,
    db: Session = Depends(get_db),
):

    portfolios = list_portfolios(db, user_id)

    result = []

    for portfolio in portfolios:

        holding_count = len(get_holdings(db, portfolio.id))

        latest_recommendation = (
            db.query(PortfolioRecommendation)
            .filter(PortfolioRecommendation.portfolio_id == portfolio.id)
            .order_by(PortfolioRecommendation.generated_at.desc())
            .first()
        )

        result.append({
            "id": portfolio.id,
            "name": portfolio.name,
            "user_id": portfolio.user_id,
            "holding_count": holding_count,
            "last_recommendation_at": (
                latest_recommendation.generated_at.isoformat()
                if latest_recommendation else None
            ),
        })

    return result


# Must be registered before GET /{portfolio_id} — FastAPI/Starlette match
# routes in registration order, and a path segment always matches a
# plain {portfolio_id} parameter structurally (coercion to int happens
# only after the match), so a static route like this one has to come
# first or it would never be reached.
@router.post("/resolve-ticker", response_model=HoldingResolution)
def resolve_ticker_endpoint(
    request: ResolveTickerRequest,
):

    return resolve_ticker(request.input)


@router.get("/{portfolio_id}")
def get_portfolio_detail(
    portfolio_id: int,
    db: Session = Depends(get_db),
):

    portfolio = get_portfolio(db, portfolio_id)

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    profile = get_portfolio_profile(db, portfolio_id)
    holdings = get_holdings(db, portfolio_id)
    document_status_summary = get_document_status_summary(db, portfolio_id)

    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "user_id": portfolio.user_id,
        "profile": {
            "risk_tolerance": profile.risk_tolerance,
            "investment_horizon": profile.investment_horizon,
            "investment_goal": profile.investment_goal,
        } if profile else None,
        "holdings": [
            {
                "id": h.id,
                "ticker": h.ticker,
                "quantity": h.quantity,
                "purchase_price": h.purchase_price,
            }
            for h in holdings
        ],
        "document_status_summary": document_status_summary,
    }


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


@router.post("/{portfolio_id}/holdings", response_model=CreatePortfolioResponse)
def add_holdings(
    portfolio_id: int,
    holdings_input: list[HoldingInput],
    db: Session = Depends(get_db),
):

    portfolio = get_portfolio(db, portfolio_id)

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    created_holdings, needs_confirmation = _resolve_and_write_holdings(
        db, portfolio_id, holdings_input
    )

    db.commit()

    return CreatePortfolioResponse(
        portfolio_id=portfolio.id,
        user_id=portfolio.user_id,
        created_holdings=created_holdings,
        needs_confirmation=needs_confirmation,
    )
