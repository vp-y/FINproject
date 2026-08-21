from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

root_agent = Agent(
    name="aegis_test_agent",
    model=LiteLlm(model="mistral/mistral-large-latest"),
    instruction="""
    You are a financial assistant.
    Answer user queries clearly.
    """
)
