from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from tools.research_tools import (
    search_financial_documents,
)
from tools.web_search_tools import (
    search_recent_company_news,
)
from tools.market_tools import (
    analyze_recent_market_move,
)


research_agent = Agent(
    name="research_agent",

    model=LiteLlm(model="mistral/mistral-large-latest"),

    instruction="""
You are a financial research specialist.

You have access to:

1. Internal financial documents.
2. Recent market data.
3. External news search.

Workflow:

- Use market data to identify recent significant movement.
- Use internal documents for structural and long-term risks.
- Use external search only for recent events.
- Never treat search snippets as unquestionable truth.
- Prefer primary and authoritative sources.
- Preserve source metadata.
- Clearly distinguish:
  historical disclosure,
  current market movement,
  and recent external events.
""",

    tools=[
        search_financial_documents,
        search_recent_company_news,
        analyze_recent_market_move,
    ],
)
