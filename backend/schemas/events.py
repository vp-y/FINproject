from pydantic import BaseModel
from typing import Literal, Optional, Any


class AgentEvent(BaseModel):

    type: Literal[
        "agent_started",
        "agent_completed",
        "tool_started",
        "tool_completed",
        "error",
        "final_result",
    ]

    agent: Optional[str] = None

    tool: Optional[str] = None

    message: str

    data: Optional[Any] = None
