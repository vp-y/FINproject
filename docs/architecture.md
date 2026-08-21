# Architecture

## Overview

Aegis is a financial assistant platform with three main pieces: a Next.js
frontend, a FastAPI backend, and an AI agent layer built on Google's Agent
Development Kit (ADK).

```
┌─────────────────┐        HTTP (axios)        ┌──────────────────┐
│  Frontend        │ ─────────────────────────▶ │  Backend          │
│  Next.js 16      │ ◀───────────────────────── │  FastAPI          │
│  (localhost:3000)│         JSON                │  (localhost:8000) │
└─────────────────┘                             └─────────┬─────────┘
                                                            │
                                        ┌───────────────────┼───────────────────┐
                                        │                   │                   │
                                        ▼                   ▼                   ▼
                                ┌───────────────┐  ┌────────────────┐  ┌────────────────┐
                                │ PostgreSQL 16  │  │ ADK Agents      │  │ (planned)       │
                                │ via Docker     │  │ via LiteLLM →   │  │ analytics/tools │
                                │ (aegis-postgres│  │ Mistral API     │  │ services         │
                                │ :5432)         │  │                 │  │                  │
                                └───────────────┘  └────────────────┘  └────────────────┘
```

## Components

### Frontend (`frontend/`)
- Next.js 16 (App Router, Turbopack), TypeScript, Tailwind CSS.
- Source lives under `frontend/src/` (`src/app` for routes, `src/lib` for
  shared code such as the API client).
- `src/lib/api.ts` exports a configured `axios` instance pointed at the
  backend (`NEXT_PUBLIC_API_URL`, defaults to `http://localhost:8000`).
- Dev server: `npm run dev` → `http://localhost:3000`.

### Backend (`backend/`)
- FastAPI app defined in `backend/main.py`.
- CORS is enabled for `http://localhost:3000` so the frontend can call it
  directly from the browser.
- Dev server: `uvicorn main:app --reload` → `http://localhost:8000`.
- Config/secrets loaded from `backend/.env` via `python-dotenv` (not
  committed — see `.gitignore`).
- Scaffolded but not yet implemented: `api/`, `models/`, `schemas/`,
  `services/`, `analytics/`, `tools/`, `utils/`. These exist as empty
  packages for upcoming work and aren't wired into `main.py` yet.

### Database
- PostgreSQL 16, run locally via `docker/docker-compose.yml`
  (container `aegis-postgres`, port `5432`, db `aegis_db`).
- `backend/database/connection.py` sets up a SQLAlchemy `engine` and
  `SessionLocal` from `DATABASE_URL` in `.env`.
- No ORM models or tables are defined yet — see
  [database_schema.md](database_schema.md) for current status.
- `alembic` is listed in `requirements.txt` for future migrations but has
  not been initialized (no `alembic.ini` / `migrations/` yet).

### Agent layer (`backend/agents/`)
- Built on `google-adk`. See [agent_design.md](agent_design.md) for details.
- Currently one test agent (`aegis_test_agent`) proving the pipeline works;
  no agents are yet exposed through the FastAPI API.
- Model calls are routed through LiteLLM to the Mistral API (not Gemini,
  despite the `google-adk` naming — ADK is just the orchestration
  framework, the model provider is swappable).

## Environment variables (`backend/.env`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string for Postgres |
| `GOOGLE_API_KEY` | Unused currently (left over from the original Gemini setup) |
| `MISTRAL_API_KEY` | Auth for the Mistral API, used by agents via LiteLLM |
| `MARKET_API_KEY` | Reserved, not yet used |
| `NEWS_API_KEY` | Reserved, not yet used |

## Not yet built

This section will need updating as the project grows. As of this writing:
- No API routes beyond the `/` health-check endpoint in `main.py`.
- No database tables/models.
- No authentication.
- Agents aren't reachable from the frontend yet — `test_adk.py` is a
  standalone script, not an HTTP endpoint.
