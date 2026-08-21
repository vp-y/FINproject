from pydantic import BaseModel
from typing import Literal


class AgentTask(BaseModel):

    portfolio_id: int | None = None

    task_type: Literal[
        "portfolio",
        "risk",
        "research",
        "scenario",
        "combined",
    ]

    user_query: str
