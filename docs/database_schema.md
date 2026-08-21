# Database Schema

## Status: not yet defined

No ORM models or tables exist in this project yet. This document currently
covers the connection setup only; it should be filled in with real tables
as `backend/models/` gets populated.

## Connection

- Engine: PostgreSQL 16, run via Docker (`docker/docker-compose.yml`,
  container `aegis-postgres`).
- Connection string (`backend/.env`):
  ```
  DATABASE_URL=postgresql://aegis:aegis123@localhost:5432/aegis_db
  ```
- `backend/database/connection.py` creates the SQLAlchemy `engine` and a
  `SessionLocal` session factory from that URL. Nothing currently imports
  or uses `SessionLocal` outside of manual testing.

## Credentials (local dev only)

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| User | `aegis` |
| Password | `aegis123` |
| Database | `aegis_db` |

These are plaintext defaults from `docker-compose.yml`, fine for local
development. They should not be reused as-is for any deployed environment.

## Migrations

`alembic` is in `backend/requirements.txt` but has not been initialized —
there is no `alembic.ini` or `migrations/` directory yet. Once real models
exist, run `alembic init migrations` from `backend/` to set up migration
tracking.

## Planned tables

Not yet designed. Fill in as `backend/models/` is built out — e.g. this is
the place to document tables like `users`, `portfolios`, `transactions`,
`agent_sessions`, etc. once they exist, along with their columns,
relationships, and indexes.
