from fastapi import APIRouter
from pydantic import BaseModel

from schemas.agent import AgentTask
from services.agent_orchestrator import run_orchestration
from agents.supervisor import classify_query_type

router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


class AnalyzeRequest(BaseModel):
    portfolio_id: int | None = None
    query: str
    # ties this REST call to the WebSocket connection opened via
    # /ws/agents/{session_id} (Step 4.14), so live events land on the
    # right client instead of a global broadcast. Optional — omitting
    # it just means no one is listening for live events on this run.
    session_id: str | None = None


@router.post("/analyze")
async def analyze(
    request: AnalyzeRequest
):

    task = AgentTask(
        portfolio_id=request.portfolio_id,
        task_type=classify_query_type(request.query),
        user_query=request.query
    )

    return await run_orchestration(task, session_id=request.session_id)
