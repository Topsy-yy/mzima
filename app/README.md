# Mzima Backend

FastAPI backend for walk-in queue management and clinician-reviewed appointment requests. The local synthetic prototype uses SQLite by default; deployments may configure PostgreSQL with `DATABASE_URL`. The locally hosted agent and MCP workflow described in the system design are not implemented yet.

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

## Local synthetic setup

Requirements: Python 3.11+ and Node.js 20+.

Run these commands from the repository root:

1. Install the backend and test dependencies: `python -m pip install -e ".[dev]"`.
2. Copy `app/.env.example` to `.env` if you need local overrides. The default is a local `mzima.db`; the database file is ignored by Git.
3. Create/update the local schema: `python -m alembic upgrade head`.
4. Add synthetic queue/request records and create local staff accounts: `python -m scripts.seed_data`. It prints randomly generated demo account passwords once; save them locally. The command refuses to seed a non-SQLite database.
5. In one terminal run `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.
6. In another terminal run `cd frontend`, `npm install`, then `npm run dev`. Open `http://localhost:5173`; Vite proxies API requests to the backend.

The patient form accepts synthetic patient identifiers only. Staff pages use the generated accounts and role checks enforced by the API. The SQLite setup is for local development and synthetic demonstrations only, not live care.

To configure PostgreSQL instead, provide a secured PostgreSQL `DATABASE_URL` in a private `.env`, then run the same migration and API commands. Never use demo accounts or development signing keys for a deployment.

Interactive API documentation is available at `/docs` while the server is running. The configured user roles are `clerk`, `nurse`, `shift_lead`, and `admin`.

This is a development prototype, not a clinical decision system. Use synthetic data only; clinical workflow changes require authorized staff decisions.