# Mzima Backend - Setup & Run Guide

## Project Structure

```
mzima/
├── app/                    # Python FastAPI backend (importable as `app`)
│   ├── adapters/           # External service adapters (FHIR, etc.)
│   ├── agent/              # AI agent workflows
│   ├── api/                # API routes (v1 endpoints)
│   ├── core/               # Config, security
│   ├── db/                 # Database session, models
│   ├── mcp/                # Model Context Protocol server
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic (queue, audit)
│   ├── main.py             # FastAPI app entry point
│   ├── pyproject.toml      # Python package config
│   ├── alembic.ini         # Alembic config (local copy)
│   ├── .env.example        # Environment template
│   ├── .venv/              # Virtual environment (created here)
│   └── BACKEND_README.md   # This file
├── migrations/             # Alembic database migrations (project root)
├── scripts/                # Utility scripts (seeding, testing)
├── .env                    # Environment variables (project root, not committed)
└── neon.ts                 # Neon config (Postgres)
```

---

## Prerequisites

- **Python 3.11+**
- **Neon account** (for managed Postgres) or local PostgreSQL
- **Node.js 20+** (for frontend, optional)

---

## Quick Start (from project root)

### 1. Setup Virtual Environment (inside `app/`)

```bash
cd app
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### 2. Install Dependencies

```bash
pip install -e .
```

This installs the `mzima-backend` package in editable mode with all dependencies.

### 3. Configure Environment

Copy the example and edit with your values:

```bash
cp app/.env.example .env
```

**Required variables in `.env` (at project root):**

```env
# Database (Neon or local Postgres)
DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/dbname"

# Security
SECRET_KEY="your-random-secret-key-min-32-chars"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=480

# App
PROJECT_NAME="Mzima Backend"
API_V1_STR="/api/v1"
ENV="development"
DEBUG=True
```

**For Neon (recommended):**
```bash
# After running `neon deploy`, these are auto-populated in .env:
DATABASE_URL="postgresql+psycopg2://neondb_owner:xxx@ep-xxx-pooler.aws.neon.tech/neondb"
DATABASE_URL_UNPOOLED="postgresql+psycopg2://neondb_owner:xxx@ep-xxx.aws.neon.tech/neondb"
NEON_BRANCH="production"
```

> **Note:** Use `postgresql+psycopg2://` dialect (not `postgresql://`) to avoid psycopg v3 libpq issues.

### 4. Run Database Migrations

```bash
# From project root
alembic upgrade head
```

This creates all tables in your Neon/Postgres database.

### 5. (Optional) Seed Test Data

```bash
python scripts/seed_data.py
```

Creates default users (`clerk1`, `nurse1`, `lead1`) and synthetic visits.

### 6. Start the Backend Server

**From project root (recommended):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**From `app/` directory:**
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **API Docs (Swagger):** http://localhost:8000/docs
- **OpenAPI JSON:** http://localhost:8000/api/v1/openapi.json
- **Health Check:** http://localhost:8000/health
- **Readiness Check:** http://localhost:8000/ready

---

## Neon Database Setup (Production)

### One-time Setup

```bash
# Install Neon CLI
npm i -g neon@latest

# Login
neon login

# Initialize project (creates neon.ts)
neon init -y --org-id YOUR_ORG_ID --project-id YOUR_PROJECT_ID --branch production --services postgres

# Deploy (provisions Postgres, pulls env vars to .env)
neon deploy
```

### Branch-Based Development

```bash
# Create a preview branch with data copy
neon checkout -b feature-branch

# Deploy schema changes to preview branch
neon deploy --branch feature-branch

# Delete when done
neon branches delete feature-branch
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness + DB connectivity |
| POST | `/api/v1/auth/login` | Login (username/password) |
| GET | `/api/v1/auth/me` | Current user info |
| GET | `/api/v1/queue` | Get live queue |
| POST | `/api/v1/visits` | Create visit (triage) |
| GET | `/api/v1/visits` | List visits |
| POST | `/api/v1/visits/{id}/triage` | Complete triage |
| POST | `/api/v1/queue/{id}/call` | Call next patient |
| POST | `/api/v1/appointments/appointment-requests` | Create appointment request |
| GET | `/api/v1/appointments/clinic/review-queue` | Pending reviews |
| POST | `/api/v1/appointments/appointment-requests/{id}/decision` | Clinician decision |

---

## Running Tests (from project root)

```bash
# Run test scripts
python scripts/test_phase5.py  # FHIR adapter + MCP tools
python scripts/test_phase6.py  # Agent safety guardrails
```

---

## Development Workflow

### Adding a New Migration

```bash
# After modifying models in app/models/
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Code Style

```bash
# Format (if black/ruff installed)
cd app && black . && ruff check . --fix
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
```bash
cd app && pip install -e .  # Reinstall package in editable mode
```

### "psycopg2.OperationalError: could not connect to server"
- Check `DATABASE_URL` in `.env` (project root)
- Ensure Neon branch is active (not suspended)
- Verify IP allowlist in Neon Console

### "ImportError: no pq wrapper available"
- Use `postgresql+psycopg2://` dialect in DATABASE_URL
- Ensure `psycopg2-binary` is installed (not `psycopg`)

### Migrations fail with "relation already exists"
```bash
# Reset to clean state (destructive!)
alembic downgrade base
alembic upgrade head
```

### "alembic: No 'script_location' key found in configuration"
- Run alembic from project root (where `alembic.ini` is symlinked/copied)
- Or use `alembic -c app/alembic.ini upgrade head` from project root

---

## Environment Files

| File | Purpose | Committed? |
|------|---------|------------|
| `app/.env.example` | Template | ✅ Yes |
| `.env` (project root) | Local overrides | ❌ No (gitignored) |
| `.env.local` (project root) | Neon auto-pulled | ❌ No |

---

## Production Deployment

1. **Set `ENV=production` and `DEBUG=False` in `.env`**
2. **Use strong `SECRET_KEY`** (generate with `openssl rand -hex 32`)
3. **Use Neon pooled connection** (`DATABASE_URL` with `-pooler` endpoint)
4. **Run behind reverse proxy** (nginx, Cloudflare, etc.)
5. **Enable HTTPS** (required for secure cookies/auth)

```bash
# Production start (with gunicorn for multi-worker)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Frontend (Optional)

The React frontend is in `src/` and `index.html` (project root):

```bash
# From project root
npm install
npm run dev      # Dev server (Vite)
npm run build    # Production build
npm run preview  # Preview production build
```

Frontend expects backend at `http://localhost:8000` (configure in `src/api.ts`).