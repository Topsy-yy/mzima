# Mzima | Tech Stack

Five-day prototype. Every choice maps directly to the design constraints:
patient data sovereignty, clinician approval gate, audit trail, and a one-command start.

---

## Overview

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph (Python) |
| MCP server | FastMCP (Python) |
| REST API | FastAPI (Python) |
| Database | Neon (PostgreSQL, serverless) |
| Schema / migrations | Prisma (TypeScript) |
| Frontend | Next.js 15 (App Router, TypeScript) |
| Styling | Tailwind CSS + shadcn/ui |
| Auth | NextAuth.js v5 |
| LLM gateway | Agent Router (https://agentrouter.org) |
| Voice | ElevenLabs |
| Validation | Pydantic v2 (backend) / Zod (frontend) |
| Local dev | Docker Compose |

---

## Backend: FastAPI

FastAPI runs the REST API, handles authentication, issues approval tokens, and writes the audit log. LangGraph and the MCP server are Python too, so keeping everything in one process avoids unnecessary service boundaries for the prototype.

**Routes:**
```
POST /api/appointment-requests
GET  /api/clinic/review-queue
POST /api/appointment-requests/{id}/decision
GET  /api/appointments/{id}
POST /api/integrations/clinic/bookings
```

**Packages:**
```
fastapi
uvicorn[standard]
pydantic>=2
python-jose[cryptography]   # JWT
passlib[bcrypt]             # password hashing
asyncpg                     # Postgres driver for Neon
python-dotenv
httpx                       # outbound HTTP for clinic adapter
```

Schema and migrations live in Prisma (Next.js side). FastAPI queries the same Neon database directly via `asyncpg`.

---

## Agent: LangGraph + FastMCP

LangGraph runs the appointment workflow as an explicit state machine: intake, slot lookup, proposal, clinician review, commit. Each step is a named node with a defined input and output. The model cannot skip steps, approve its own proposals, or write directly to the booking queue.

FastMCP exposes three tools the agent calls:

| Tool | What it does |
|---|---|
| `get_appointment_slots` | Reads available slots from the database |
| `score_and_propose_route` | Scores the request against facility rules and saves a pending proposal |
| `review_and_commit` | Commits a clinician-approved decision with identity, reason, and audit record |

Every tool call is logged before it returns.

**Packages:**
```
langgraph
langchain-openai        # OpenAI-compatible SDK pointed at Agent Router
fastmcp
openai                  # base SDK for Agent Router OpenAI surface
```

---

## Database: Neon

Neon is a serverless Postgres provider. Each team member gets their own database branch in seconds from the Neon dashboard, so there is no shared dev database to step on. The connection string is standard Postgres, so Prisma, FastAPI, and the read-only MCP server all connect the same way.

**Tables:**
```
appointment_requests    patient intake, structured fields, status
appointment_slots       facility-seeded synthetic availability
proposals               pending agent proposals (never a live queue change)
clinician_decisions     approved / edited / rejected, with identity and reason
audit_events            every tool call: actor, inputs, output, timestamp
```

---

## Schema and Migrations: Prisma

Prisma owns the schema definition and runs migrations. The schema file lives in the Next.js codebase (`prisma/schema.prisma`) and is the single source of truth for the database structure. FastAPI reads from and writes to the same tables via raw `asyncpg` queries.

**Packages:**
```
prisma                   # CLI and migration engine
@prisma/client           # generated type-safe client
@prisma/adapter-neon     # Neon serverless adapter
@neondatabase/serverless # Neon HTTP driver
```

**Common commands:**
```bash
npx prisma db push           # apply schema changes without a migration file (prototype)
npx prisma migrate dev       # create a named migration (when history matters)
npx prisma studio            # visual data browser
```

---

## Frontend: Next.js 15

Next.js serves both the patient request flow and the clinician review dashboard as separate route groups within one application. Server components handle data fetching for the clinician queue so the page renders with data on load rather than showing an empty table while a client-side request completes.

**Route groups:**

| Group | Path | Who uses it |
|---|---|---|
| Patient flow | `/(patient)/request` | Patients or clerk-assisted intake |
| Clinician dashboard | `/(clinic)/review` | Authenticated clinicians and staff |

Auth is handled by NextAuth.js v5 with a credentials provider that validates against FastAPI's `/auth/token` endpoint. The session carries the user role (`patient`, `staff`, `clinician`) which gates both routes and UI actions.

**Packages:**
```
next@15
react@19
typescript
tailwindcss
@shadcn/ui
next-auth@5
zod
@tanstack/react-query        # data fetching and cache for the review queue
sonner                       # toast notifications for approve / reject actions
prisma
@prisma/client
@prisma/adapter-neon
@neondatabase/serverless
```

---

## LLM Gateway: Agent Router

Agent Router sits between the agent and the model. The agent sends a standard request; Agent Router routes it to the configured model. Credentials stay out of the agent code.

| Surface | Base URL | Used by |
|---|---|---|
| OpenAI-compatible | `https://agentrouter.org/v1` | LangGraph via `langchain-openai` |
| Anthropic-compatible | `https://agentrouter.org` | Claude Code, Kiro |

One `AGENTROUTER_API_KEY` from the dashboard covers both. No Anthropic account needed.

Default model: `claude-opus-4-8`

---

## Voice: ElevenLabs

ElevenLabs handles text-to-speech output for the patient-facing flow, for example reading back a confirmation or a hold message. It is not used for transcription or for any response that contains personal appointment details.

Rules that apply before any ElevenLabs call:
- The text passed to ElevenLabs must not contain patient names, symptoms, or appointment specifics
- Generic prompts only: "Your request has been received. Please wait for staff."
- Local TTS is the fallback if ElevenLabs is unavailable or the content rules cannot be met

**Package:**
```
elevenlabs          # Python SDK for TTS output
```

For patient speech input (transcription), the prototype uses the browser Web Speech API locally. No patient audio leaves the browser.

---

## Local Dev: Docker Compose

```bash
docker compose up
```

| Service | Stack | Port |
|---|---|---|
| `api` | FastAPI + LangGraph agent | 8000 |
| `web` | Next.js dev server | 3000 |

Neon replaces a local Postgres container. Set `DATABASE_URL` in `.env` and the services connect on start. Run `make seed` to populate synthetic slots and patient cases.

---

## Business Model

Mzima is built for public health facilities in Kenya and similar markets where scheduling is done manually and appointment queues are managed by staff without digital tools.

**How it generates revenue:**

Mzima is licensed to clinics and hospital networks as a software service. Pricing is per facility per month, scaled by patient volume. There is no per-API-call cost passed to the facility.

**Three tiers:**

| Tier | Who it is for | What is included |
|---|---|---|
| Clinic | Single outpatient facility | Core booking workflow, clinician approval, audit log |
| Network | Hospital group or county health system | Multi-facility, shared routing rules, aggregated reporting |
| Enterprise | National health bodies or NGO partners | Custom HMIS integration, data residency controls, dedicated support |

**Additional revenue paths:**

- Setup and onboarding fee for HMIS adapter configuration at each new facility
- Training and change management for clinical staff
- A reporting add-on that gives facility managers anonymised throughput and wait-time data

**Why this works in the target market:**

Facilities pay for tools that reduce staff time spent on manual queue management and that give clinicians a documented, auditable record of routing decisions. Mzima does both. The audit trail also supports facilities working toward accreditation or donor reporting requirements.

The prototype is built with synthetic data and no live patient records. Any commercial deployment requires facility approval, a data processing agreement, and in-country hosting for all patient data.
