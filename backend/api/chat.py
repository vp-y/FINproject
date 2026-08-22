import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from database.connection import SessionLocal
from database.models import ChatMessage
from services.chat_service import answer_chat_message


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):

    conversation_id: str | None = None
    message: str


@router.post("/{portfolio_id}")
async def chat(
    portfolio_id: int,
    request: ChatRequest,
):

    conversation_id = request.conversation_id or str(uuid.uuid4())

    return await answer_chat_message(portfolio_id, conversation_id, request.message)


@router.get("/{portfolio_id}/{conversation_id}")
def get_history(
    portfolio_id: int,
    conversation_id: str,
):

    db = SessionLocal()

    try:
        rows = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.portfolio_id == portfolio_id,
                ChatMessage.conversation_id == conversation_id,
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
    finally:
        db.close()

    return [
        {
            "role": row.role,
            "content": row.content,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
