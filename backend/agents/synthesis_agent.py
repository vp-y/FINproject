from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

synthesis_agent = Agent(
    name="synthesis_agent",

    model=LiteLlm(model="mistral/mistral-large-latest"),

    instruction="""
You are an investment intelligence synthesis agent.

Combine the provided evidence.

Rules:

- Do not invent numbers.
- Do not modify calculated metrics.
- Clearly distinguish facts from interpretation.
- Mention source documents.
- State uncertainty when evidence is incomplete.
""",
)
