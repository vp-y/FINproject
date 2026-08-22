import uuid

from fastapi import APIRouter, BackgroundTasks

from database.connection import SessionLocal
from database.models import HoldingDocument
from services.onboarding_service import (
    create_pending_documents,
    run_onboarding_collection,
)


router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"],
)

# A holding still in one of these states hasn't finished collection yet.
IN_PROGRESS_STATUSES = {"pending", "fetching", "indexing"}


@router.post("/{portfolio_id}/start-collection")
def start_collection(
    portfolio_id: int,
    background_tasks: BackgroundTasks,
    session_id: str | None = None,
):

    holding_count = create_pending_documents(portfolio_id)

    background_tasks.add_task(
        run_onboarding_collection,
        portfolio_id,
        session_id or str(uuid.uuid4()),
    )

    return {
        "status": "started",
        "portfolio_id": portfolio_id,
        "holding_count": holding_count,
    }


@router.get("/{portfolio_id}/status")
def get_status(
    portfolio_id: int,
):

    db = SessionLocal()

    try:
        rows = (
            db.query(HoldingDocument)
            .filter(HoldingDocument.portfolio_id == portfolio_id)
            .all()
        )
    finally:
        db.close()

    holdings = [
        {
            "ticker": row.ticker,
            "status": row.status,
            "document_path": row.document_path,
            "chunk_count": row.chunk_count,
            "error": row.error,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
        for row in rows
    ]

    statuses = {h["status"] for h in holdings}

    if not holdings:
        overall_status = "not_started"
    elif statuses & IN_PROGRESS_STATUSES:
        overall_status = "in_progress"
    elif "failed" in statuses:
        overall_status = "completed_with_errors"
    else:
        overall_status = "completed"

    return {
        "portfolio_id": portfolio_id,
        "holdings": holdings,
        "overall_status": overall_status,
    }
