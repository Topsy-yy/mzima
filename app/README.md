# Mzima Backend

An early FastAPI backend for walk-in queue management and clinician-reviewed appointment requests. The API uses SQLAlchemy, Alembic, and PostgreSQL. It does not currently include the agent or MCP workflow described in the repository's intended system design.

## Implemented behavior

- Walk-in check-in records age band, visit type, and red flags. Any true red-flag value marks the visit as fast-track.
- The queue ranks fast-track visits first, then visits waiting at least 120 minutes, then the highest age-weighted wait score. The score is `minutes_waited * age_weight`; `under_5` and `over_65` use a weight of `1.5`, and other age bands use `1.0`.
- Staff can call a queued visit and complete its triage. Call overrides and workflow actions are written to audit records.
- Appointment requests can be submitted and reviewed. Shift leads and admins can approve or reject a request, with the decision and reason recorded.
- Role checks protect selected staff actions; not every read or submission endpoint currently requires authentication.

## API endpoints

All versioned endpoints use the `/api/v1` prefix.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/login` | Obtain a bearer token |
| `GET` | `/auth/me` | Read the authenticated user |
| `POST` | `/visits` | Check in a walk-in visit |
| `GET` | `/queue` | List visits in queue order |
| `POST` | `/queue/{visit_id}/call` | Call a visit, optionally recording an override reason |
| `POST` | `/visits/{visit_id}/triage` | Record triage category and destination |
| `POST` | `/appointments/appointment-requests` | Submit an appointment request |
| `GET` | `/appointments/clinic/review-queue` | List pending requests |
| `POST` | `/appointments/appointment-requests/{request_id}/decision` | Record an approval or rejection |
| `GET` | `/appointments/appointments/{request_id}` | Read appointment request details |

Health checks are available at `GET /health` and `GET /ready`; the latter checks database connectivity.

## Local setup

Requirements: Python 3.11+ and a running PostgreSQL server.

1. Create a PostgreSQL database and user. In a PostgreSQL admin shell, run `CREATE USER mzima_user;` and `CREATE DATABASE mzima_db OWNER mzima_user;`, then set the user's password interactively with `\\password mzima_user`. Do not put a real password in shell history.
2. From the repository root, create a local settings file from the template: `cp app/.env.example .env`. Set `POSTGRES_PASSWORD`, `DATABASE_URL`, and `SECRET_KEY` to local development values. `.env` is excluded from Git; do not commit it.
3. Install the project and development dependencies: `python -m pip install -e ".[dev]"`.
4. Apply database migrations: `alembic upgrade head`.
5. Start the API: `uvicorn app.main:app --reload`.

Interactive API documentation is available at `/docs` while the server is running. The configured user roles are `clerk`, `nurse`, `shift_lead`, and `admin`.

This is a development prototype, not a clinical decision system. Use synthetic data only; clinical workflow changes require authorized staff decisions.