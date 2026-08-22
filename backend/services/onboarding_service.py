import asyncio
from datetime import datetime, timezone

from database.connection import SessionLocal
from database.models import HoldingDocument, Holding
from services.event_emitter import emit_event
from data_pipeline.pipeline import process_holding_row


def _update_holding_document(
    holding_id: int, portfolio_id: int, ticker: str, status: str, **fields
):
    """Upserts the HoldingDocument row for one holding. Self-healing
    (creates the row if it doesn't already exist) rather than assuming
    create_pending_documents always ran first, since on_status callbacks
    fire from a background task that can't easily surface a missing-row
    error to anyone."""

    db = SessionLocal()

    try:
        row = (
            db.query(HoldingDocument)
            .filter(HoldingDocument.holding_id == holding_id)
            .first()
        )

        if row is None:
            row = HoldingDocument(
                holding_id=holding_id,
                portfolio_id=portfolio_id,
                ticker=ticker,
            )
            db.add(row)

        row.status = status

        if "company_name" in fields:
            row.company_name = fields["company_name"]
        if "document_path" in fields:
            row.document_path = fields["document_path"]
        if "chunk_count" in fields:
            row.chunk_count = fields["chunk_count"]

        row.error = fields.get("error")
        row.updated_at = datetime.now(timezone.utc)

        db.commit()

    finally:
        db.close()


def create_pending_documents(portfolio_id: int) -> int:
    """Fast, DB-only step run synchronously by the onboarding API
    handler before backgrounding the real collection work, so a client
    watching GET /onboarding/{id}/status immediately sees the full
    holding list at status='pending' rather than an empty one."""

    db = SessionLocal()

    try:
        holdings = (
            db.query(Holding)
            .filter(Holding.portfolio_id == portfolio_id)
            .all()
        )
    finally:
        db.close()

    for holding in holdings:
        _update_holding_document(
            holding.id, portfolio_id, holding.ticker, "pending"
        )

    return len(holdings)


async def run_onboarding_collection(portfolio_id: int, session_id: str):
    """Background task (kicked off by
    POST /onboarding/{id}/start-collection): fetches + RAG-ingests each
    of the portfolio's holdings' most recent 10-K one at a time, updating
    that holding's HoldingDocument row and emitting WebSocket progress
    events at each transition.

    process_holding_row is fully synchronous (requests.get to SEC EDGAR,
    then the Gemini embedding calls) — calling it directly would block
    this whole async function's event loop for the entire duration
    (confirmed while testing this: a single large 10-K blocked even an
    unrelated GET /onboarding/{id}/status request for ~2 minutes, and no
    WS event could be delivered until the call returned). Routed through
    asyncio.to_thread so the event loop stays free to serve other
    requests and flush queued WS events while this runs. Per holding it
    degrades gracefully — one ticker failing (e.g. embedding quota
    exhausted) doesn't stop the rest of the batch from being attempted."""

    db = SessionLocal()
    try:
        holdings = (
            db.query(Holding)
            .filter(Holding.portfolio_id == portfolio_id)
            .all()
        )
    finally:
        db.close()

    for holding in holdings:

        await emit_event(session_id, {
            "type": "document_fetch_started",
            "agent": "onboarding",
            "tool": "process_holding_row",
            "message": f"Collecting documents for {holding.ticker}",
            "data": {"ticker": holding.ticker},
        })

        def on_status(status, **fields):
            _update_holding_document(
                holding.id, portfolio_id, holding.ticker, status, **fields
            )

        try:
            await asyncio.to_thread(
                process_holding_row, {"ticker": holding.ticker}, on_status
            )
        except Exception as e:
            _update_holding_document(
                holding.id, portfolio_id, holding.ticker, "failed", error=str(e)
            )

        db = SessionLocal()
        try:
            final_row = (
                db.query(HoldingDocument)
                .filter(HoldingDocument.holding_id == holding.id)
                .first()
            )
            final_status = final_row.status if final_row else "failed"
        finally:
            db.close()

        event_type = (
            "document_indexed" if final_status == "indexed" else "document_failed"
        )

        await emit_event(session_id, {
            "type": event_type,
            "agent": "onboarding",
            "message": f"{holding.ticker}: {final_status}",
            "data": {"ticker": holding.ticker, "status": final_status},
        })

    await emit_event(session_id, {
        "type": "onboarding_completed",
        "agent": "onboarding",
        "message": "Document collection finished",
    })
