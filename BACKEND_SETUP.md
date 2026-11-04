# Mzima Backend Setup

The FastAPI application is in the `backend/` Python package. Run commands from the repository root unless a step says otherwise. The backend dependencies and virtual environment are managed by the backend project in `backend/`.

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) installed
- A PostgreSQL database, local or hosted

Check the tools:

```bash
python --version
uv --version
```

## First-time setup

From the repository root:

```bash
uv sync --project backend
```

This creates/updates `backend/.venv` and installs the dependencies declared in `backend/pyproject.toml` and `backend/uv.lock`.

Configure the root `.env` file, which is loaded when commands run from the repository root. Start from the example if needed:

```bash
cp .env.example .env
```

Set at least `DATABASE_URL` to a reachable PostgreSQL database and set a private `SECRET_KEY` for development. `AGENTROUTER_API_KEY` is only needed for the optional extraction integration. Do not commit real credentials. The example uses a local development database URL; the application also has a development fallback, but database-backed endpoints require a working database.

## Start the server

From the repository root, use:

```bash
uv run --project backend uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The equivalent command using the backend virtualenv directly is:

```bash
backend/.venv/bin/python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

If already in `backend/`, run:

```bash
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

`backend.main:app` is the actual FastAPI import path. Stop the development server with Ctrl+C.

Endpoints:

- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Readiness (checks the database): http://127.0.0.1:8000/ready
- OpenAPI JSON: http://127.0.0.1:8000/api/v1/openapi.json

## Database migrations

From the repository root:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

If your terminal is already in `backend/`:

```bash
uv run alembic -c alembic.ini upgrade head
```

## Tests

Run the backend test suite from the repository root:

```bash
uv run --project backend pytest
```

The phase helper scripts are at the repository root and can be run with:

```bash
uv run --project backend python scripts/test_phase5.py
uv run --project backend python scripts/test_phase6.py
```
