from datetime import datetime, timezone

from database.connection import SessionLocal
from database.models import ChatMessage, PortfolioRecommendation
from tools.portfolio_tools import get_portfolio_holdings
from rag.retriever import retrieve
from services.agent_orchestrator import run_agent_with_retry
from agents.synthesis_agent import synthesis_agent

# ADK sessions aren't persisted across HTTP requests today (run_agent
# builds a fresh InMemoryRunner+session every call) — this ChatMessage
# table IS the multi-turn memory instead. Only the last few turns are
# re-fed into the prompt each time, not the whole history, to keep the
# prompt (and the Mistral call it drives) bounded regardless of how
# long a conversation runs.
CHAT_HISTORY_LIMIT = 10
CHAT_RAG_TOP_K = 5


def _load_recent_messages(portfolio_id: int, conversation_id: str) -> list[ChatMessage]:

    db = SessionLocal()
    try:
        rows = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.portfolio_id == portfolio_id,
                ChatMessage.conversation_id == conversation_id,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(CHAT_HISTORY_LIMIT)
            .all()
        )
    finally:
        db.close()

    return list(reversed(rows))  # oldest-first for the prompt


def _save_message(portfolio_id: int, conversation_id: str, role: str, content: str):

    db = SessionLocal()
    try:
        db.add(ChatMessage(
            portfolio_id=portfolio_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()
    finally:
        db.close()


def _latest_recommendation(portfolio_id: int):

    db = SessionLocal()
    try:
        return (
            db.query(PortfolioRecommendation)
            .filter(PortfolioRecommendation.portfolio_id == portfolio_id)
            .order_by(PortfolioRecommendation.generated_at.desc())
            .first()
        )
    finally:
        db.close()


def _build_chat_prompt(history, holdings, recommendation_row, rag_chunks, message):

    history_text = "\n".join(
        f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
        for m in history
    ) or "(no prior conversation)"

    holdings_text = ", ".join(
        f"{h['ticker']} ({h['quantity']} shares)" for h in holdings
    ) or "(no holdings)"

    recommendation_text = (
        recommendation_row.summary
        if recommendation_row and recommendation_row.summary
        else "(no recommendation has been generated yet for this portfolio)"
    )

    sources = []
    evidence_lines = []

    for chunk in rag_chunks:

        metadata = chunk.get("metadata", {})

        evidence_lines.append(
            f"- {metadata.get('document_name')} (page {metadata.get('page_number')}): "
            f"{chunk.get('text', '')[:500]}"
        )

        sources.append({
            "document": metadata.get("document_name"),
            "page": metadata.get("page_number"),
            "company": metadata.get("company"),
        })

    evidence_text = "\n".join(evidence_lines) or "(no relevant filing excerpts found)"

    prompt = f"""
You are Aegis, a portfolio-specific financial assistant. Answer the
user's question using only the context below — the portfolio's
holdings, its most recent recommendation analysis, and relevant
excerpts from indexed company filings.

Conversation so far:
{history_text}

Portfolio holdings: {holdings_text}

Most recent recommendation summary:
{recommendation_text}

Relevant filing excerpts:
{evidence_text}

User's new message: {message}

Rules:
- Do not invent numbers or facts not present in the context above.
- If the context doesn't cover the question, say so plainly rather than guessing.
- Cite which filing excerpt supports a claim about a specific company, if any.
- Write in plain prose paragraphs only — no markdown formatting (no #
  headers, ** bold, | tables, or --- rules).
- This is analysis, not individualized financial advice.
"""

    return prompt, sources


async def answer_chat_message(portfolio_id: int, conversation_id: str, message: str) -> dict:
    """Portfolio-specific chatbot turn. Deliberately does NOT go through
    run_orchestration/route_request — chat needs to be fast (one LLM
    call, not a multi-step workflow) and must reuse the *last persisted*
    recommendation rather than regenerating it every turn, consistent
    with the rate-limit discipline used throughout this feature."""

    history = _load_recent_messages(portfolio_id, conversation_id)

    holdings_result = get_portfolio_holdings(portfolio_id)
    holdings = holdings_result.get("holdings", [])
    tickers = [h["ticker"] for h in holdings]

    recommendation_row = _latest_recommendation(portfolio_id)

    rag_chunks = retrieve(message, tickers=tickers, top_k=CHAT_RAG_TOP_K) if tickers else []

    prompt, sources = _build_chat_prompt(
        history, holdings, recommendation_row, rag_chunks, message
    )

    # synthesis_agent has no tools, so there's nothing for run_agent to
    # emit WS events about here — session_id is only used for that
    # routing, so reusing conversation_id (rather than a live dashboard
    # WS session_id, which this function has no access to) is harmless.
    #
    # run_agent_with_retry only retries a *silent* empty response (the
    # rate-limit signature LiteLLM/ADK swallow internally) — a real
    # provider error (bad credentials, insufficient credits, a genuine
    # 4xx/5xx) raises instead, and every other LLM call site in this
    # codebase (agent_orchestrator.py's workflows) wraps that in a
    # try/except so one failed call degrades gracefully rather than
    # crashing the whole request. This call needs the same guard, or an
    # account/provider hiccup would 500 the endpoint and silently lose
    # the user's message (nothing gets persisted below).
    try:
        response_text, _ = await run_agent_with_retry(
            synthesis_agent, prompt, conversation_id
        )
    except Exception as e:
        response_text = None
        print(f"chat_service: synthesis_agent failed ({e.__class__.__name__}): {e}")

    answer = response_text or (
        "I couldn't reach the assistant model just now — please try again "
        "in a moment."
    )

    _save_message(portfolio_id, conversation_id, "user", message)
    _save_message(portfolio_id, conversation_id, "assistant", answer)

    return {
        "conversation_id": conversation_id,
        "message": {"role": "assistant", "content": answer},
        "sources": sources,
    }
