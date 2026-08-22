from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from tools.risk_tools import (
    calculate_portfolio_risk,
    analyze_portfolio_risk,
)


risk_agent = Agent(
    name="risk_agent",

    model=LiteLlm(model="anthropic/claude-sonnet-5"),

    instruction="""
You are a quantitative portfolio risk analyst.

You analyze:

- volatility
- Value at Risk
- Sharpe ratio
- downside risk
- concentration risk

Rules:

- Never invent numerical metrics.
- Prefer analyze_portfolio_risk when given a portfolio_id — it
  retrieves real holdings and market data and computes returns for you.
- Use calculate_portfolio_risk only if you already have a returns
  series to work from.
- Explain what each metric means.
- Clearly state assumptions.
- Do not provide unsupported investment recommendations.
""",

    tools=[
        calculate_portfolio_risk,
        analyze_portfolio_risk,
    ],
)
