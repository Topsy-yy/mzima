# Mzima Backend - Setup & Run Guide

This FastAPI application is in the `backend/` Python package. Run commands from the repository root unless a step says otherwise. Dependencies are managed by `backend/pyproject.toml` and `backend/uv.lock`; the virtual environment is `backend/.venv`. The app reads `.env` relative to the current working directory, so the commands below use the repository-root `.env` file. The backend supports PostgreSQL, including Neon, and optional Synthea-derived synthetic data.

## Current scope

The backend now includes:

- Walk-in queue indexing and clinical/staff review workflows
- Deterministic flow metrics, bottleneck detection, recommendations, and simulation
- Synthetic patient observations and IITT-derived warning-sign alerts
- Optional AgentRouter-based free-text extraction
- Imported Synthea synthetic encounter and observation data

It remains a **synthetic-data prototype only**. It is not approved for live patient care.

---

## Prerequisites

- Python **3.11+**
- **uv** (recommended) for dependency and environment management
- A reachable PostgreSQL database for database-backed endpoints
- Environment file at the repository root (`.env`)

From the repository root, check tools:

```bash
uv --version
python --version
```

---

## 1. Install dependencies (repository root)

From the repository root:

```bash
uv sync --project backend
```

This creates or updates `backend/.venv` using `backend/pyproject.toml` and `backend/uv.lock`.

## 2. Configure environment

Create the repository-root `.env` from the example if it does not already exist:

```bash
cp .env.example .env
```

Set `DATABASE_URL` to a reachable PostgreSQL database and configure a private `SECRET_KEY`. `AGENTROUTER_API_KEY` is optional and only needed for the extraction integration. Never commit real credentials. Database-backed endpoints require a working database.

## 3. Run database migrations (as needed)

From the repository root:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

If your terminal is already in `backend/`:

```bash
uv run alembic -c alembic.ini upgrade head
```

## 4. Start the backend

From the repository root:

```bash
uv run --project backend uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

If your terminal is already in `backend/`:

```bash
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Use Ctrl+C to stop the development server. `backend.main:app` is the application import path.

Endpoints:

- Swagger API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Readiness (checks the database): http://127.0.0.1:8000/ready
- OpenAPI JSON: http://127.0.0.1:8000/api/v1/openapi.json

## 5. Seed data (optional)

Run these scripts from the repository root after configuring the database:

```bash
uv run --project backend python scripts/seed_data.py
uv run --project backend python scripts/seed_flow.py
uv run --project backend python scripts/import_synthea.py
```

## Key API groups

| POST | `/api/v1/visits` | Walk-in check-in |
| GET | `/api/v1/queue` | Walk-in queue |
| POST | `/api/v1/queue/{visit_id}/call` | Call next patient |
| POST | `/api/v1/visits/{visit_id}/triage` | Complete triage |
| GET | `/api/v1/flow/summary` | Flow metrics |
| GET | `/api/v1/flow/clinical-alerts` | Evidence-backed warning-sign alerts |
| POST | `/api/v1/flow/bottleneck-scan` | Detect bottlenecks |
| POST | `/api/v1/flow/recommendations/scan` | Generate operational recommendations |
| POST | `/api/v1/flow/simulations` | Stakeholder-free operational simulation |
| POST | `/api/v1/flow/observations` | Create synthetic/prototype observation set |
| POST | `/api/v1/flow/observations/extract` | Optional AgentRouter extraction |

---

## Agent Router / AI extraction

The extraction endpoint converts free text into structured fields and returns `requires_human_review: true`. It does not diagnose or assign priority.

Test:

```bash
curl -X POST http://localhost:8000/api/v1/flow/observations/extract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Patient has fever 39.2, fast breathing, severe headache, confused."}'
```

Important status: extraction reached AgentRouter, but the configured key was rejected with **401 Unauthorized / unauthorized client detected** during this environment test. This is a remote access/authorization issue, not a local import issue. Verify the AgentRouter key, account permissions, and outbound network access before relying on extraction.

---

## Testing helpers

```bash
uv run --project backend python scripts/test_phase5.py
uv run --project backend python scripts/test_phase6.py
```

No comprehensive automated test suite has been added yet for the new flow endpoints.

---

## Development notes

### Relative imports and package install

```bash
uv pip install -e .
```

Reinstall if you see:

```text
ModuleNotFoundError: No module named 'backend'
```

### Migrations

```bash
uv run --project backend alembic -c backend/alembic.ini revision --autogenerate -m "description"
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

### Stack and style

- Backend package root: `backend/`
- Migrations run from project root
- Database schema is additive where possible
- Flow endpoints are deterministic except optional extraction

---

## Troubleshooting

### `uvicorn: command not found`

Use:

```bash
uv run --project backend uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Run the command above from the repository root. From `backend/`, use `uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`.

### `alembic: command not found`

Use:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

### `ModuleNotFoundError: No module named 'backend'`

From the repository root, run Alembic with its backend project and config:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
```

### `GET /v1/models` used to return 404

The backend now returns a compatibility response for `/v1/models`.

### AgentRouter extraction returns 401

Verify:

- `AGENTROUTER_API_KEY` is valid
- `BASE_URL` points to the AgentRouter endpoint
- The deployment environment can reach `agentrouter.org`
- Account-level access is enabled for the key

### `GET /health` returns 200 but `GET /ready` fails

Check `DATABASE_URL`, Neon branch status, and network connectivity.

---

## Safety boundary

This backend is for synthetic-data development only unless a pilot facility, clinical owners, data controller, privacy review, retention policy, and approved hosting environment are in place. It must not be described as live-care ready. Every clinical decision belongs to qualified healthcare staff.
