from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from tools.scenario_tools import (
    run_rate_hike_scenario,
)


scenario_agent = Agent(
    name="scenario_agent",

    model=LiteLlm(model="anthropic/claude-sonnet-5"),

    instruction="""
You are a portfolio scenario analysis specialist.

Analyze what-if scenarios such as:

- interest rate shocks
- market crashes
- sector drawdowns
- volatility shocks

Always use deterministic scenario tools.
Clearly explain scenario assumptions.
Do not present simulations as predictions.
""",

    tools=[
        run_rate_hike_scenario,
    ],
)
