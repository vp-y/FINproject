"""
Supervisor.

Per Step 3.13's guidance, the first working version of routing is
deterministic Python (see services/agent_orchestrator.route_request),
not an LLM classifying every request:

    Deterministic routing -> Working system -> LLM supervisor -> Advanced autonomy

This module is the integration point for that upgrade later — an
LLM-based classifier can replace classify_intent() below without any
other code needing to change, since agent_orchestrator only depends on
this function's return value (one of AgentTask.task_type's literals).
"""

from services.agent_orchestrator import route_request

RISK_KEYWORDS = ["risk", "volatil", "var", "sharpe", "downside"]
RESEARCH_KEYWORDS = [
    "report", "filing", "risk factor", "document", "10-k", "disclos",
    "company information", "supporting", "why is", "why did", "why has",
    "background", "tell me about", "what data"
]
SCENARIO_KEYWORDS = ["what if", "scenario", "stress test", "rate hike", "shock", "crash"]


def classify_query_type(query: str) -> str:
    """Deterministic keyword-based intent classification — the 'day
    one' version per Step 3.13's guidance ('deterministic routing ->
    working system -> LLM supervisor'). The API layer uses this to
    fill in AgentTask.task_type when a caller only sends free text,
    without needing an LLM call just to figure out routing."""

    q = query.lower()

    wants_scenario = any(kw in q for kw in SCENARIO_KEYWORDS)
    wants_risk = any(kw in q for kw in RISK_KEYWORDS)
    wants_research = any(kw in q for kw in RESEARCH_KEYWORDS)

    if wants_scenario:
        return "scenario"

    if wants_risk:
        # The "risk" workflow (Step 5.13) already runs its own internal
        # research step as part of the pipeline, so a query mentioning
        # both risk and research keywords still just needs "risk" — no
        # need to fall back to the plainer combined loop.
        return "risk"

    if wants_research:
        return "research"

    # neither clearly signaled — gather everything rather than guess
    return "combined"


def classify_intent(task):
    """Currently just delegates to deterministic routing. Swap this
    for an LLM-based classifier once the deterministic system is
    proven, per the phase's own recommended order."""

    return route_request(task)
