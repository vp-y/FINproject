# Aegis

## Prerequisites

- Python 3.12+
- Node.js
- Docker Desktop

## Required API keys

Create `backend/.env` (see `backend/.env` for the current template) with these
keys. All three have free tiers.

| Variable | Used for | Get it from |
|---|---|---|
| `DATABASE_URL` | Local Postgres connection | Pre-filled — no signup needed, matches `docker/docker-compose.yml` |
| `GOOGLE_API_KEY` | RAG document embeddings + answer generation (Gemini) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `MISTRAL_API_KEY` | All agent reasoning/tool-calling (Supervisor, Portfolio, Risk, Research, Scenario, Synthesis agents) | [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys) |
| `TAVILY_API_KEY` | Web/news search (recent company events) | [app.tavily.com](https://app.tavily.com) |

`MARKET_API_KEY` and `NEWS_API_KEY` also exist in `.env` but are currently
unused — nothing in the codebase reads them. Market data (Yahoo Finance) and
SEC filing lookups (SEC EDGAR) don't need a key at all.

Free-tier limits to know about: Mistral's free tier rate-limits fairly
aggressively under sustained multi-agent use, and Gemini's embedding quota
(separate from its chat quota) caps at 1000 requests/day. Neither blocks
normal use, but heavy testing can hit them — see the "Improving reliability"
notes below if you want to reduce that.

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
uvicorn main:app --reload