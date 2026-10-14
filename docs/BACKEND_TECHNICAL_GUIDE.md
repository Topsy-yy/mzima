# Mzima Backend Technical Guide

## Overview

Mzima Backend is a **FastAPI**-based REST API for capacity-aware queue management and clinic triage. Built with Python 3.11+, it uses **PostgreSQL** for persistence, **SQLAlchemy 2.0** for ORM, **Alembic** for migrations, and **JWT/OAuth2** for authentication.

---

## Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Python | ≥ 3.11 |
| PostgreSQL | ≥ 14 |
| pip/uv | latest |

### 1. Clone & Install

```bash
cd /home/taz/desktop/ai/mzima
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your PostgreSQL credentials
```

Required variables in `.env`:
```env
DATABASE_URL=postgresql://mzima_user:your_secure_password@localhost:5432/mzima_db
SECRET_KEY=your_32+_char_random_string
```

### 3. Database Setup

```bash
# Create database (run once)
createdb -U postgres mzima_db

# Run migrations
alembic upgrade head
```

### 4. Start Server

```bash
# Development (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Verify

- **Health**: `GET http://localhost:8000/health`
- **Readiness**: `GET http://localhost:8000/ready`
- **API Docs**: `http://localhost:8000/api/v1/openapi.json` (Swagger at `/docs`)

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app factory, health/ready endpoints
│   ├── core/
│   │   ├── config.py           # Pydantic Settings (env-driven config)
│   │   └── security.py         # Argon2 hashing, JWT token creation/validation
│   ├── db/
│   │   └── session.py          # SQLAlchemy engine, session factory, Base
│   ├── models/
│   │   └── domain.py           # SQLAlchemy ORM models (User, Visit, AuditEvent...)
│   ├── schemas/
│   │   ├── domain.py           # Pydantic models for visits, queue events
│   │   └── auth.py             # Token, UserResponse schemas
│   ├── api/
│   │   ├── deps.py             # FastAPI dependencies (DB, auth, RBAC)
│   │   └── v1/
│   │       ├── router.py       # APIRouter aggregation
│   │       └── endpoints/
│   │           ├── auth.py     # POST /auth/login, GET /auth/me
│   │           ├── appointments.py
│   │           └── queue.py
│   ├── services/
│   │   ├── queue/engine.py     # Queue prioritization logic (SATS/TEWS/ETAT)
│   │   └── audit/service.py    # Audit logging
│   ├── adapters/
│   │   └── clinic/mock_fhir.py # External clinic system integration stub
│   └── mcp/
│       └── server.py           # Model Context Protocol server
├── migrations/                 # Alembic migration scripts
├── alembic.ini                 # Alembic configuration
├── pyproject.toml              # Project metadata & dependencies
└── .env.example                # Environment template
```

---

## Technical Architecture

### Request Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   FastAPI    │────▶│  Dependency │────▶│  Business   │
│  (Frontend) │     │   Router     │     │  Injection  │     │   Logic     │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                           │                    │                    │
                           ▼                    ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                    │  Middleware │     │  get_db()   │     │  Services   │
                    │ (CORS, etc) │     │  Session    │     │  (queue,    │
                    └─────────────┘     └─────────────┘     │   audit)    │
                                                         └─────────────┘
                                                                │
                                                                ▼
                                                         ┌─────────────┐
                                                         │  Database   │
                                                         │ (PostgreSQL)│
                                                         └─────────────┘
```

### Key Components

| Layer | Responsibility | Key Files |
|-------|----------------|-----------|
| **Transport** | HTTP routing, OpenAPI, validation | `main.py`, `api/v1/router.py` |
| **Dependencies** | DB session, auth, RBAC | `api/deps.py` |
| **Auth** | JWT (HS256), Argon2 hashing, OAuth2PasswordBearer | `core/security.py`, `api/v1/endpoints/auth.py` |
| **Data Access** | SQLAlchemy 2.0 ORM, declarative models | `models/domain.py`, `db/session.py` |
| **Business Logic** | Queue prioritization, audit, appointments | `services/queue/engine.py` |
| **External** | FHIR adapter, MCP server | `adapters/`, `mcp/` |

### Data Models (Core)

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `User` | Staff authentication & RBAC | `id`, `username`, `hashed_password`, `role` (CLERK/NURSE/SHIFT_LEAD/ADMIN) |
| `Visit` | Walk-in patient queue entry | `token_number`, `age_band`, `visit_type`, `is_fast_track`, `red_flags`, `status`, `triage_category`, `destination` |
| `QueueEvent` | Immutable audit trail of queue actions | `visit_id`, `actor_id`, `event_type` (CALL, OVERRIDE, PROMOTION, FLAG_RAISED), `reason_code` |
| `AppointmentRequest` | Scheduled appointment requests | `patient_identifier`, `requested_specialty`, `status` |
| `ClinicianDecision` | Clinician review outcomes | `request_id`, `clinician_id`, `decision` (APPROVE/REJECT/MODIFY) |
| `AuditEvent` | System-wide audit log | `actor_id`, `action`, `entity_type`, `entity_id`, `payload` |

---

## Data Flow Examples

### 1. Walk-in Patient Registration

```
POST /api/v1/queue/walk-in
    │
    ▼
Validate payload (age_band, visit_type, red_flags)
    │
    ▼
Generate token_number (format: W-YYYYMMDD-NNNN)
    │
    ▼
Calculate priority_score:
    - Base: age_band weight + visit_type weight
    - Fast-track: +1000 if is_fast_track
    - Red flags: +500 per flag
    │
    ▼
Insert Visit (status=IN_QUEUE)
    │
    ▼
Insert QueueEvent (event_type=REGISTER)
    │
    ▼
Return { token_number, estimated_wait, position }
```

### 2. Clinician Calls Next Patient

```
POST /api/v1/queue/call-next
    │
    ▼
Auth: Requires NURSE or SHIFT_LEAD role (RoleChecker)
    │
    ▼
Query: SELECT * FROM visits WHERE status=IN_QUEUE ORDER BY priority_score DESC, arrival_time ASC LIMIT 1
    │
    ▼
Update Visit: status=CALLED, triage_start_time=now()
    │
    ▼
Insert QueueEvent (event_type=CALL, actor_id=current_user)
    │
    ▼
Return { visit_id, token_number, patient_info }
```

### 3. Triage Completion

```
POST /api/v1/queue/{visit_id}/triage
    │
    ▼
Validate: triage_category (SATS/TEWS/ETAT), destination
    │
    ▼
Update Visit: status=TRIAGED, triage_end_time=now(), triage_category, destination
    │
    ▼
Insert QueueEvent (event_type=TRIAGE_COMPLETE)
    │
    ▼
AuditEvent: action=TRIAGE_COMPLETE, entity=Visit
    │
    ▼
Return updated Visit
```

---

## Security

### Authentication

| Aspect | Implementation |
|--------|----------------|
| **Scheme** | OAuth2 Password Flow (Bearer JWT) |
| **Token** | JWT HS256, 8-hour expiry (configurable) |
| **Payload** | `sub` (username), `role` (CLERK/NURSE/SHIFT_LEAD/ADMIN), `exp` |
| **Login** | `POST /api/v1/auth/login` with `username`/`password` (form-data) |
| **Validation** | `OAuth2PasswordBearer` + `jwt.decode()` in `get_current_user()` |

### Password Security

- **Hashing**: Argon2 (via `passlib[argon2]`) — memory-hard, resistant to GPU cracking
- **Verification**: Constant-time comparison via `pwd_context.verify()`
- **Storage**: Only `hashed_password` stored in DB

### Authorization (RBAC)

```python
# Role hierarchy (ascending privilege)
CLERK < NURSE < SHIFT_LEAD < ADMIN

# Usage in endpoints
from app.api.deps import RoleChecker

@router.post("/admin-only")
def admin_endpoint(user: User = Depends(RoleChecker([RoleEnum.ADMIN]))):
    ...
```

| Endpoint | Required Role |
|----------|---------------|
| `POST /auth/login` | Public |
| `GET /auth/me` | Any authenticated |
| `POST /queue/walk-in` | CLERK+ |
| `POST /queue/call-next` | NURSE+ |
| `POST /queue/{id}/triage` | NURSE+ |
| `POST /queue/override` | SHIFT_LEAD+ |
| `POST /appointments/*` | CLERK+ (create), NURSE+ (review) |

### Security Checklist for Production

- [ ] Generate strong `SECRET_KEY` (32+ random bytes)
- [ ] Use `ENV=production`, `DEBUG=False`
- [ ] Set `POSTGRES_PASSWORD` to strong value
- [ ] Enable TLS (reverse proxy: nginx/Caddy + certbot)
- [ ] Configure CORS in `main.py` for your frontend domain
- [ ] Set `ACCESS_TOKEN_EXPIRE_MINUTES` lower (e.g., 30-60)
- [ ] Enable PostgreSQL SSL (`sslmode=require` in `DATABASE_URL`)
- [ ] Rotate `SECRET_KEY` periodically
- [ ] Add rate limiting (e.g., `slowapi` on `/auth/login`)

### Audit Trail

All mutating operations emit `AuditEvent`:
- Actor (user), action, entity type/ID, timestamp, JSON payload
- Queryable via `GET /api/v1/audit` (if endpoint exposed)
- Immutable — no UPDATE/DELETE on `audit_events` table

---

## Configuration Reference

### Environment Variables (`core/config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | "Mzima Backend" | API title in OpenAPI |
| `API_V1_STR` | "/api/v1" | API version prefix |
| `ENV` | "development" | Environment name |
| `DEBUG` | True | Debug mode |
| `DATABASE_URL` | (computed) | Full SQLAlchemy URL |
| `SECRET_KEY` | "dev_secret..." | JWT signing key |
| `ALGORITHM` | "HS256" | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 480 | Token TTL |

---

## Development Workflow

### Running Tests

```bash
pytest -v
# or with coverage
pytest --cov=app --cov-report=term-missing
```

### Adding Migrations

```bash
# After model changes
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Code Quality

```bash
# Type checking (if mypy configured)
mypy app/

# Linting
ruff check app/
```

---

## API Endpoints Summary

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Liveness probe | Public |
| GET | `/ready` | Readiness (DB check) | Public |
| POST | `/api/v1/auth/login` | Obtain JWT | Public |
| GET | `/api/v1/auth/me` | Current user profile | Bearer |
| POST | `/api/v1/queue/walk-in` | Register walk-in | CLERK+ |
| GET | `/api/v1/queue/status` | Queue dashboard | CLERK+ |
| POST | `/api/v1/queue/call-next` | Call next patient | NURSE+ |
| POST | `/api/v1/queue/{id}/triage` | Complete triage | NURSE+ |
| POST | `/api/v1/queue/override` | Priority override | SHIFT_LEAD+ |
| POST | `/api/v1/appointments/` | Create request | CLERK+ |
| GET | `/api/v1/appointments/` | List requests | NURSE+ |
| POST | `/api/v1/appointments/{id}/decide` | Clinician decision | NURSE+ |

---

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| `ModuleNotFoundError: app` | Run from project root, ensure `pip install -e .` |
| DB connection refused | Check PostgreSQL running, `DATABASE_URL` correct |
| `alembic: command not found` | Activate venv, `pip install -e ".[dev]"` |
| 401 Unauthorized | Check `SECRET_KEY` matches, token not expired |
| 403 Forbidden | Verify user role in DB matches `RoleEnum` |
| Migration conflicts | `alembic history`, resolve manually, `alembic upgrade head` |

---

## Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [python-jose JWT](https://python-jose.readthedocs.io/)
- [passlib Argon2](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html)