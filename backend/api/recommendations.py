import uuid

from fastapi import APIRouter

from database.connection import SessionLocal
from database.models import PortfolioRecommendation
from services.agent_orchestrator import run_recommendation_workflow


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.post("/{portfolio_id}/generate")
async def generate(
    portfolio_id: int,
    session_id: str | None = None,
):
    """Runs the full recommendation workflow synchronously — bounded to
    at most 2 real LLM calls (research capped at 3 tickers, one
    synthesis call), the same budget class as the existing risk
    workflow, which is already called synchronously today."""

    result = await run_recommendation_workflow(
        portfolio_id,
        "Analyze my portfolio and recommend what to hold, reduce, sell, "
        "or increase, with alternatives.",
        session_id or str(uuid.uuid4()),
    )

    return result


@router.get("/{portfolio_id}/latest")
def latest(
    portfolio_id: int,
):
    """The most recently generated recommendation for this portfolio, so
    the dashboard can reload without recomputing (and re-spending LLM
    calls) on every visit."""

    db = SessionLocal()

    try:
        row = (
            db.query(PortfolioRecommendation)
            .filter(PortfolioRecommendation.portfolio_id == portfolio_id)
            .order_by(PortfolioRecommendation.generated_at.desc())
            .first()
        )
    finally:
        db.close()

    if not row:
        return {"status": "none"}

    return {
        "status": "found",
        "portfolio_id": row.portfolio_id,
        "session_id": row.session_id,
        "generated_at": row.generated_at.isoformat() if row.generated_at else None,
        "run_status": row.status,
        "summary": row.summary,
        **row.payload,
    }
