# Mzima Backend --- Capacity-Aware Queue & Clinic Triage API

Mzima is a capacity-aware queue management and outpatient triage system
tailored for Level 6 public hospitals in Kenya. This repository contains
the local backend REST API, database architecture, mock clinic
integration adapters, and agent-authorization safety boundaries built
with FastAPI and PostgreSQL.

------------------------------------------------------------------------

## Technical Stack & Architecture

-   **Framework:** Python 3.11+ / FastAPI (async ASGI)
-   **Database:** PostgreSQL (native `systemd` service)
-   **ORM and migrations:** SQLAlchemy 2.0 and Alembic
-   **Security and authentication:** JWT bearer tokens with Argon2
    password hashing
-   **Data and simulation:** Pandas and NumPy for synthetic arrival and
    visit generation
-   **Integrations:** Mock HL7 FHIR adapter and read-only Model Context
    Protocol (MCP) server

------------------------------------------------------------------------

## Core System & Security Principles

### 1. Role-Based Access Control (RBAC)

Route-level permissions are enforced for the following roles:

-   `clerk`
-   `nurse`
-   `shift_lead`
-   `admin`

### 2. Deterministic Triage Score Engine

-   **Fast-track priority:** A red-flag door-screen result triggers
    immediate fast-tracking to the top of the queue.
-   **Weighted score ranking:** Calculated as `minutes_waited * weight`.
    The `under_5` and `over_65` age bands carry a `1.5` multiplier; the
    default multiplier is `1.0`.
-   **Wait-cap promotions:** Patients waiting at least 120 minutes are
    automatically promoted.

### 3. Append-Only Audit Logging

Audit logs durably capture actors, actions, timestamps, before-and-after
states, and reason codes for nurse call overrides.

### 4. Human-in-the-Loop AI Guardrails

AI models and automated agent workflows can generate booking proposals
(`PROPOSED_BY_AGENT`), but cannot self-approve or commit clinical
workflow decisions. Explicit clinician approval is required before a
proposed booking can be committed.

------------------------------------------------------------------------

## Complete Implementation Summary (Phases 1--6)

### Phase 1 --- Foundation & Health

-   FastAPI application setup
-   Native PostgreSQL database connectivity
-   `/health` and `/ready` endpoints

### Phase 2 --- Database Schema & Synthetic Seeding

-   SQLAlchemy models for `users`, `visits`, `queue_events`,
    `appointment_requests`, `clinician_decisions`, and `audit_events`
-   Alembic migrations
-   Seed script for test users and seven days of synthetic walk-in data

### Phase 3 --- Authentication, RBAC & Audit Middleware

-   Argon2 password hashing
-   JWT bearer-token login
-   Role-based access-control dependencies
-   Append-only audit event logging

### Phase 4 --- Core Workflows & REST APIs

-   Walk-in check-in
-   Dynamic queue ranking
-   Nurse token calling with override-reason tracking
-   Clinical triage logging
-   Appointment review queues

### Phase 5 --- Clinic Adapter & Read-Only MCP

-   Mock HMIS adapter mapping appointment records to HL7 FHIR
    `Appointment` resources
-   Thread-safe, read-only MCP server for agent inspection over
    synthetic data

### Phase 6 --- Agent Workflow & Safety Boundaries

-   LangGraph/agent integration guardrails
-   Agent-generated booking proposals require explicit human clinician
    sign-off (`APPROVE` or `REJECT`) before the workflow state can
    transition

------------------------------------------------------------------------

## Local Setup & Quickstart (Native Arch Linux)

### Prerequisites

-   Python 3.11+
-   PostgreSQL
-   Git

### 1. Initialize PostgreSQL

Enable and start PostgreSQL:

``` bash
sudo systemctl enable --now postgresql
```

Create the database role and database:

``` bash
sudo -u postgres createuser --createdb mzima_user
sudo -u postgres createdb -O mzima_user mzima_db
sudo -u postgres psql -c "ALTER USER mzima_user WITH PASSWORD 'mzima_dev_password';"
```

> **Development only:** The credentials shown here are placeholders for
> a local synthetic-data environment. Do not use these credentials or a
> development secret in production.

### 2. Configure Environment Variables

Copy the example environment file:

``` bash
cp .env.example .env
```

Ensure `.env` contains the appropriate local settings:

``` dotenv
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=mzima_user
POSTGRES_PASSWORD=mzima_dev_password
POSTGRES_DB=mzima_db
DATABASE_URL=postgresql+psycopg2://mzima_user:mzima_dev_password@localhost:5432/mzima_db
SECRET_KEY=dev_secret_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

Keep `.env` out of version control. Use a unique, securely generated
secret outside development.

### 3. Create a Virtual Environment and Install Packages

From the repository root:

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install python-multipart
```

### 4. Apply Migrations and Seed Synthetic Data

Run the database migrations and seed script:

``` bash
alembic upgrade head
python scripts/seed_data.py
```

The seed script is expected to create the following development
accounts:

  Username   Password         Role
  ---------- ---------------- --------------
  `clerk1`   `clerkpass123`   `clerk`
  `nurse1`   `nursepass123`   `nurse`
  `lead1`    `leadpass123`    `shift_lead`

These are development-only credentials. Do not reuse them outside a
local synthetic-data environment.

### 5. Launch the API Server

Start the Uvicorn development server:

``` bash
uvicorn app.main:app --reload
```

API documentation:

-   **Swagger UI:** <http://127.0.0.1:8000/docs>
-   **ReDoc:** <http://127.0.0.1:8000/redoc>
-   **OpenAPI JSON:** <http://127.0.0.1:8000/api/v1/openapi.json>

------------------------------------------------------------------------

## API Endpoints Reference

Versioned endpoints are prefixed with `/api/v1`, except for the system
health endpoints.

  ------------------------------------------------------------------------------------------------------------------------------------
  Domain         Method         Endpoint                                                            Description        Access
  -------------- -------------- ------------------------------------------------------------------- ------------------ ---------------
  System         `GET`          `/health`                                                           Application        Public
                                                                                                    liveness check     

  System         `GET`          `/ready`                                                            PostgreSQL         Public
                                                                                                    readiness check    

  Auth           `POST`         `/api/v1/auth/login`                                                Authenticate a     Public
                                                                                                    user and return a  
                                                                                                    JWT bearer token   

  Auth           `GET`          `/api/v1/auth/me`                                                   Return the current Authenticated
                                                                                                    authenticated      
                                                                                                    user's context     

  Walk-in queue  `POST`         `/api/v1/visits`                                                    Patient check-in   `clerk`,
                                                                                                    and door red-flag  `admin`
                                                                                                    intake             

  Walk-in queue  `GET`          `/api/v1/queue`                                                     List queue tokens  As configured
                                                                                                    in calculated      by the API
                                                                                                    priority order     

  Walk-in queue  `POST`         `/api/v1/queue/{visit_id}/call`                                     Call a token and   `nurse`,
                                                                                                    record any nurse   `shift_lead`,
                                                                                                    override reason    `admin`

  Walk-in queue  `POST`         `/api/v1/visits/{visit_id}/triage`                                  Log triage         `nurse`,
                                                                                                    category           `shift_lead`,
                                                                                                    (SATS/TEWS/ETAT)   `admin`
                                                                                                    and routing        

  Appointments   `POST`         `/api/v1/appointments/appointment-requests`                         Submit an          As configured
                                                                                                    appointment        by the API
                                                                                                    request            

  Appointments   `GET`          `/api/v1/appointments/clinic/review-queue`                          List requests      `shift_lead`,
                                                                                                    awaiting clinician `admin`
                                                                                                    decision           

  Appointments   `POST`         `/api/v1/appointments/appointment-requests/{request_id}/decision`   Record clinician   `shift_lead`,
                                                                                                    approval or        `admin`
                                                                                                    rejection          

  Appointments   `GET`          `/api/v1/appointments/appointments/{request_id}`                    Retrieve           As configured
                                                                                                    appointment        by the API
                                                                                                    request status and 
                                                                                                    details            
  ------------------------------------------------------------------------------------------------------------------------------------

> Endpoint paths and permissions should match the actual route
> definitions in the application. Verify them in Swagger UI at `/docs`
> when running the backend.

------------------------------------------------------------------------

## Verification & Testing

Run the standalone verification scripts from the project root:

``` bash
# Verify the Phase 5 FHIR adapter and read-only MCP tools
python scripts/test_phase5.py

# Verify Phase 6 agent proposals and safety guardrails
python scripts/test_phase6.py
```

These scripts require the corresponding implementation and configuration
to be present.

------------------------------------------------------------------------

## Development Notes

-   Use synthetic data only in the prototype.
-   Treat model-generated content as untrusted input and validate it
    against deterministic, facility-approved rules.
-   Keep clinician approval separate from agent proposal generation.
-   Use idempotency keys for booking commits and never repeat a commit
    with a new key merely because a request timed out.
-   Do not claim integration with a real HMIS/FHIR system until the
    target facility and its supported interface have been verified.
