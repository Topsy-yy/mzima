# Mzima | Appointment and Routing Co-pilot

Mzima is a synthetic-data prototype for outpatient appointment requests and clinic queue operations. It currently provides a FastAPI API for authentication, appointment-request review, walk-in queue operations, and audit events, plus a React staff/patient interface. The planned local agent and MCP appointment-routing workflow are not yet implemented.

**Safety boundary:** this prototype is not for live care. It is not a diagnostic system and does not autonomously triage patients or change bookings or queue positions. Use synthetic data only.

## Project Layout

The repository root is the single project root. There is one Python backend (`app/`) and one frontend (`frontend/`); migrations, seed data, docs, and tests also live at the root. The old standalone `backend/` scaffold is retired.

```text
app/                 FastAPI API, domain logic, database, and adapters
frontend/            React + TypeScript + Vite application
migrations/          Alembic schema migrations
scripts/             Synthetic-data seeding and phase checks
tests/               API smoke tests
docs/                Architecture, privacy, and evaluation documentation
.env.example         Local API configuration template
pyproject.toml       Python package and development dependencies
```

## Start Locally

### Prerequisites

- Python 3.11 or newer
- Node.js and npm
- PostgreSQL 14 or newer, running locally

### 1. Configure PostgreSQL

Create a local development role and database (choose a local password):

```sql
CREATE USER mzima_user WITH PASSWORD 'replace-this-local-password';
CREATE DATABASE mzima_db OWNER mzima_user;
```

For example, open the PostgreSQL shell with `sudo -u postgres psql` on Linux, run those statements, then exit with `\q`.

### 2. Configure the API

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` and set `POSTGRES_PASSWORD`, `DATABASE_URL` to the same credentials, and `SECRET_KEY` to a random development value. Keep `.env` private and out of version control. `.env.example` contains only local placeholders.

Create and activate a virtual environment, then install the app and development tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Apply the schema and seed synthetic records:

```bash
alembic upgrade head
python scripts/seed_data.py
```

Start the API from the repository root:

```bash
uvicorn app.main:app --reload
```

The API is at `http://127.0.0.1:8000`; interactive API docs are at `http://127.0.0.1:8000/docs`. `GET /health` checks process liveness and `GET /ready` checks database connectivity.

### 3. Start the frontend

In a second terminal, from the repository root:

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

Open `http://localhost:5173`. Vite proxies `/api`, `/health`, and `/ready` to `http://127.0.0.1:8000`. Set `MZIMA_API_URL` in the frontend environment if the API uses a different address.

### Checks

With the Python development dependencies installed:

```bash
pytest
npm --prefix frontend run build
```

The API smoke test does not require a live database; migration, readiness, and seeded workflow checks do. Use [frontend/README.md](frontend/README.md) for frontend/API scope and limitations.

## Project Status and Safety

The requirements and intended architecture are documented in [docs/MZIMA_SYSTEM_DESIGN.md](docs/MZIMA_SYSTEM_DESIGN.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). [docs/EVALS.md](docs/EVALS.md) is a test plan, not a report of measured results. The current API does not yet implement the described local model, MCP agent flow, appointment slots, or agent proposal/commit workflow.

Do not use real patient information in issues, commits, prompts, demos, or third-party tools. The prototype and its seeded accounts are for local synthetic data only. Review [docs/DATA_AND_PRIVACY.md](docs/DATA_AND_PRIVACY.md) before changing data handling or considering a pilot.

## Licence

See [LICENSE](LICENSE).
