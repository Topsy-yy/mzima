# Mzima | Team Roles

Three-person team working toward a five-day prototype: patient appointment request → local agent → MCP tools → clinician approval gate → committed synthetic booking → audit log.

---

## Taz — Agent Engineer + Research Lead

**Core responsibility:** the brain of the system. Owns the LangGraph agent, the MCP server implementation, and all research that informs technical decisions.

**Areas:**
- LangGraph state machine design and implementation (intake → slot lookup → proposal → clinician review → commit → audit)
- Mzima MCP server — all three tools: `get_appointment_slots`, `score_and_propose_route`, `review_and_commit`
- Trust boundaries, approval token logic, and idempotency on the commit path
- Local open-weight model selection, hosting setup (Ollama / vLLM), and prompt engineering
- Agent recovery paths: bounded retries, stale slot detection, staff handoff
- Security: prompt injection defence, data egress blocking, audit log integrity
- Research: open-weight model options for Kenyan context, local TTS/STT alternatives to ElevenLabs, PostgreSQL MCP server evaluation, privacy and data sovereignty requirements

See **[TAZ_TASKS.md](TAZ_TASKS.md)** for the full task and research breakdown.

---

## Kisiwani — Backend + API Engineer

**Core responsibility:** the plumbing. Owns the REST API layer, the PostgreSQL schema, the clinic adapter, and infrastructure that connects the agent to the outside world.

**Areas:**
- Local REST API (`POST /api/appointment-requests`, `GET /api/clinic/review-queue`, `POST /api/appointment-requests/{id}/decision`, `GET /api/appointments/{id}`)
- Authentication and role-based access control for patient, staff, and clinician routes
- PostgreSQL schema design: appointment requests, slots, proposals, audit events, clinician decisions
- Self-hosted read-only PostgreSQL MCP server setup (synthetic data only)
- Clinic scheduling adapter — mock local HMIS/FHIR API for prototype demos
- One-command local start: Docker Compose or equivalent with seeded synthetic data
- Environment configuration, secrets management, and local networking

---

## Vee — Frontend + Clinician UX

**Core responsibility:** the faces of the system. Owns the patient-facing request flow and the clinician review dashboard.

**Areas:**
- Patient web interface: appointment request form, voice-assisted input (local STT where possible), confirmation screen
- Clinician review dashboard: pending proposals queue, approve/edit/reject actions, evidence display, audit trail view
- Staff handoff screen: clear messaging when the agent cannot proceed
- Integration with the REST API (Kisiwani's endpoints)
- Accessibility and basic Kenyan English / Kiswahili UI copy
- Demo recording support: UI must make agent tool calls and decisions visible for the submission demo

---

## Cross-cutting ownership

| Concern | Owner |
|---|---|
| Synthetic patient data generation | Kisiwani (schema) + Taz (case coverage for evals) |
| EVALS.md — running and recording results | Taz (agent traces) + Kisiwani (infra) + Vee (UI flows) |
| DATA_AND_PRIVACY.md compliance | Taz (research lead) reviews; whole team upholds |
| Submission demo recording | Vee records; Taz narrates agent decisions |
| Final README and submission checklist | Taz drafts; Kisiwani + Vee review |
