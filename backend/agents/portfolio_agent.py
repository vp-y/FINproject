from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from tools.portfolio_tools import (
    get_portfolio_holdings,
)


portfolio_agent = Agent(
    name="portfolio_agent",

    model=LiteLlm(model="anthropic/claude-sonnet-5"),

    instruction="""
You are a portfolio intelligence specialist.

Your responsibilities:

1. Retrieve portfolio holdings.
2. Explain portfolio composition.
3. Identify concentration.
4. Identify major exposures.

Rules:

- Always use portfolio tools for portfolio facts.
- Never invent holdings.
- Clearly separate retrieved data from interpretation.
- Do not calculate financial metrics yourself when a tool exists.
""",

    tools=[
        get_portfolio_holdings,
    ],
)
