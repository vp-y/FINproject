# Agent Design

## Framework

Agents are built with [Google ADK](https://github.com/google/adk-python)
(`google-adk`), which provides the agent runtime, session handling, and
runner infrastructure. ADK is model-agnostic: despite the "Google" naming,
model calls don't have to go to Gemini.

## Model provider: Mistral (via LiteLLM)

Agents in this project call the **Mistral API**, not Gemini. ADK's
`LiteLlm` wrapper (`google.adk.models.lite_llm.LiteLlm`) routes model
calls through [LiteLLM](https://docs.litellm.ai/), which supports Mistral
natively.

```python
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
```

- Model string format: `mistral/<model-name>` (LiteLLM convention).
- Currently using `mistral-large-latest`. Swap to `mistral-small-latest`
  for a cheaper/faster model if quality trade-off is acceptable.
- Auth: `MISTRAL_API_KEY` in `backend/.env`, read automatically by
  LiteLLM — no need to pass it explicitly in code.
- `GOOGLE_API_KEY` in `.env` is a leftover from before the Mistral switch
  and is currently unused.

## Current agents

### `aegis_test_agent` (`backend/agents/test_agent.py`)

A minimal proof-of-concept agent used to validate the ADK + LiteLLM +
Mistral pipeline end to end. Single-turn, no tools, no memory beyond the
in-memory session used to test it.

- Instruction: acts as a general financial assistant, answers queries
  clearly.
- Tested via `backend/test_adk.py`, which spins up an `InMemoryRunner`,
  creates a throwaway session, sends one message, and prints the reply.
  This script is for local testing only — it is not an HTTP endpoint and
  isn't called from the frontend.

## Testing an agent locally

```bash
cd backend
venv\Scripts\activate
python test_adk.py
```

This runs the agent against a single hardcoded question ("What is a mutual
fund?") and prints the response to the console.

## Planned / not yet built

- `backend/tools/` is scaffolded but empty — no custom tools have been
  attached to any agent yet.
- No agent is exposed through the FastAPI backend (`backend/api/` is also
  empty). Agents currently only run via the standalone test script.
- No persistent session storage — the test setup uses `InMemoryRunner`,
  which discards state on process exit. A real deployment would need a
  persistent session/session-service backing (e.g. backed by the Postgres
  database once that's wired up).
- No multi-agent orchestration yet (routing between specialized agents,
  sub-agents, etc.) — just the one flat test agent.
