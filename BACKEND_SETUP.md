# Mzima Backend — Setup & Run Guide

The backend lives in the `backend/` directory at the project root.

## Prerequisites

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) installed (`pip install uv` or the official installer)
- PostgreSQL running locally (or update `DATABASE_URL` in your `.env`)

## First-time setup

```bash
# From the project root
cd backend
uv sync          # installs dependencies into backend/.venv
cp .env.example .env   # then fill in your secrets
```

## Running the server

### Option A — from the project root (recommended)

```bash
cd /path/to/mzima
uv run --project backend uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B — from inside backend/

```bash
cd /path/to/mzima/backend
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

> **Why `backend.main:app` and not `main:app`?**  
> Python resolves module names from the working directory. When you run from the project root, the package is `backend`, so the entry point is `backend.main:app`. Running from inside `backend/` also works because `backend/` is on `sys.path` via the editable install — but you still use `backend.main:app` since the package name is `backend`.

## Environment variables

Copy `backend/.env.example` to `backend/.env` and set:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key (change in production) |
| `AGENTROUTER_API_KEY` | API key for the agent router service |

## Database migrations

```bash
# From the project root:
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

## Running tests

```bash
cd backend
uv run pytest
```
