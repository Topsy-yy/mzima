# Mzima Backend - Setup & Run Guide

This backend is a FastAPI application stored in `app/` but **started from the project root**. It uses the project-root `.env` file, Neon PostgreSQL, and optional Synthea-derived synthetic data.

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
- **uv** (recommended) instead of pip
- PostgreSQL, preferably Neon
- Environment file at the project root (`.env`)

Check tools:

```bash
uv --version
python --version
```

---

## 1. Create the environment (project root)

```bash
cd /home/taz/desktop/ai/mzima  # or your project root
uv venv
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

---

## 2. Install dependencies with uv

Use uv, not pip:

```bash
uv pip install -e .
```

This installs the `mzima-backend` package in editable mode into `.venv`.

Alternative, after dependencies are already declared:

```bash
uv sync
```

---

## 3. Configure environment

Copy the consolidated example:

```bash
cp .env.example .env
```

Then edit `.env`. Required values:

```env
# Database
DATABASE_URL="postgresql://user:password@host:5432/dbname"
DATABASE_URL_UNPOOLED="postgresql://user:password@host:5432/dbname"

# Security (either variable is accepted)
SECRET_KEY="replace-with-a-random-development-secret"
# API_SECRET_KEY="replace-with-a-random-development-secret"

JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=480

# Agent Router (optional, for assistive extraction)
AGENTROUTER_API_KEY="sk-your-agentrouter-key-here"
BASE_URL="https://agentrouter.org/v1"
MODEL_NAME="gpt-4o-mini"

# App
PROJECT_NAME="Mzima Backend"
API_V1_STR="/api/v1"
APP_ENV="development"
DEBUG=True
```

Important:

- The backend reads `.env` from the **project root** when started from the project root.
- `API_SECRET_KEY` and `JWT_EXPIRE_MINUTES` are accepted as aliases for `SECRET_KEY` and `ACCESS_TOKEN_EXPIRE_MINUTES`.
- AgentRouter is optional and prototype-only. Do not send real patient data to a hosted LLM.

---

## 4. Run database migrations

From the project root, use uv to run Alembic:

```bash
uv run alembic upgrade head
```

Do not run `alembic` directly unless it is already on your PATH.

---

## 5. Seed data

Create base staff and synthetic walk-in visits:

```bash
uv run python scripts/seed_data.py
```

Create flow reference data:

```bash
uv run python scripts/seed_flow.py
```

Import Synthea synthetic encounter and observation data:

```bash
uv run python scripts/import_synthea.py
```

The Synthea importer replaces flow visits/observations/clinical alerts and leaves users, stations, staffing, thresholds, and clinical rules intact.

---

## 6. Start the backend

Use uv from the project root:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If `uvicorn` is not on your PATH, do not call it directly. `uv run` resolves it from `.venv`.

Alternative with the virtualenv activated:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:

- Swagger API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/ready
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

---

## OpenAI-compatible compatibility route

Some clients probe `/v1/models`. The backend returns a small compatibility response at:

```text
GET /v1/models
```

It returns the configured `AGENTROUTER_MODEL` value so the endpoint does not produce a 404. It is a routing compatibility response, not a model-hosting endpoint.

---

## Key API groups

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Process liveness |
| GET | `/ready` | Database connectivity |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Current user |
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
uv run python scripts/test_phase5.py
uv run python scripts/test_phase6.py
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
ModuleNotFoundError: No module named 'app'
```

### Migrations

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### Stack and style

- Backend package root: `app/`
- Migrations run from project root
- Database schema is additive where possible
- Flow endpoints are deterministic except optional extraction

---

## Troubleshooting

### `uvicorn: command not found`

Use:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Do not call `uvicorn` directly unless `.venv/bin` is on `PATH`.

### `alembic: command not found`

Use:

```bash
uv run alembic upgrade head
```

### `ModuleNotFoundError: No module named 'app'`

Reinstall the project with uv:

```bash
uv pip install -e .
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
