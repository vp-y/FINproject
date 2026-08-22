# Aegis

## Prerequisites

- Python 3.12+
- Node.js
- Docker Desktop

## Required API keys

Create `backend/.env` (see `backend/.env` for the current template) with these
keys.

| Variable | Used for | Get it from |
|---|---|---|
| `DATABASE_URL` | Local Postgres connection | Pre-filled — no signup needed, matches `docker/docker-compose.yml` |
| `GOOGLE_API_KEY` | RAG document embeddings + answer generation (Gemini) — free tier | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `ANTHROPIC_API_KEY` | All agent reasoning/tool-calling (Portfolio, Risk, Research, Scenario, Synthesis agents, and the portfolio chatbot) — paid, requires billing credits on the account before any call succeeds, no free tier | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) (add credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)) |
| `TAVILY_API_KEY` | Web/news search (recent company events) — free tier | [app.tavily.com](https://app.tavily.com) |

`MARKET_API_KEY` and `NEWS_API_KEY` also exist in `.env` but are currently
unused — nothing in the codebase reads them. Market data (Yahoo Finance) and
SEC filing lookups (SEC EDGAR) don't need a key at all. `MISTRAL_API_KEY` is
also unused today — every agent was switched from Mistral to Claude
(`anthropic/claude-sonnet-5` via LiteLLM); the key can stay in `.env` harmlessly
or be removed.

Free-tier limits to know about: Gemini's embedding quota (separate from its
chat quota) caps at 1000 requests/day — heavy RAG-ingestion testing (onboarding
many portfolios in one day) can hit it. Claude has no free tier at all — the
account needs real billing credits before the Portfolio/Risk/Research/Scenario/
Synthesis agents or the chatbot can respond; a `RESOURCE_EXHAUSTED` (Gemini) or
"credit balance is too low" (Anthropic) error in the backend log means one of
these two limits was hit, not a bug.

## 1. Start the database

```bash
cd docker
docker compose up -d
```

Verify it's running:

```bash
docker ps
```

You should see `aegis-postgres` and `aegis-qdrant` listening.

## 2. Run the backend

```bash
cd backend
```

Activate the virtual environment:

```powershell
# PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# activate
venv\Scripts\activate.bat
```

Install dependencies (first time only, or after `requirements.txt` changes):

```bash
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn main:app --reload
```

Backend runs at [http://localhost:8000](http://localhost:8000). Swagger docs
(every route, testable without the frontend) at
[http://localhost:8000/docs](http://localhost:8000/docs).

## 3. Run the frontend

```bash
cd frontend
```

Install dependencies (first time only, or after `package.json` changes):

```bash
npm install
```

Start the dev server:

```bash
npm run dev
```

Frontend runs at [http://localhost:3000](http://localhost:3000).
