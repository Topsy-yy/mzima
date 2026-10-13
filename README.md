# Mzima | Appointment and Routing Co-pilot

Mzima is a prototype concept for helping patients request an early outpatient appointment and helping facility staff review where that appointment belongs. A locally hosted reasoning agent gathers structured information, checks slots and facility-approved routing guidance, and proposes a sector and priority. A named clinician must approve, edit, or reject any proposal before it can affect a booking or queue position.

**Safety boundary:** Mzima is not a diagnostic system and does not autonomously triage, refer, raise deterioration flags, or change queue position. The five-day prototype is for synthetic cases and a simulated single-facility workflow. It is not for live care.

## What makes it an agent

The agent plans a bounded workflow, calls reusable MCP tools, validates tool results, asks follow-up questions when needed, retries safe reads, and hands off when uncertain. Its own MCP server has three tools: read appointment slots, score and save a pending route proposal, and commit a clinician-approved decision. Tool inputs, outputs, timestamps and approval identity are logged.

The full task runs on an open-weight model hosted in-country. Patient data must not leave the country. Any frontier-model comparison uses synthetic data only. ElevenLabs is limited to generic, non-personal audio unless an in-country deployment and data handling are verified; patient speech and personalized appointment details stay local.

## Project status

The repository includes an early FastAPI backend for walk-in queue management, authentication, audit events, and clinician-reviewed appointment requests. It does not yet implement the locally hosted agent or MCP workflow described in the intended architecture, and there are no measured evaluation results. The requirements and intended architecture are captured in [MZIMA_SYSTEM_DESIGN.md](MZIMA_SYSTEM_DESIGN.md) and [ARCHITECTURE.md](ARCHITECTURE.md). [EVALS.md](EVALS.md) remains a test plan until an implementation produces real pass/fail results.

## Intended sub-theme and workflow

**Sub-theme:** responsible agentic AI for access to care and outpatient operations.  
**Facility:** one participating outpatient facility; selection pending.  
**Workflow:** patient requests earliest appointment → local agent proposes a sector/priority → named clinician reviews → approved appointment enters the queue.

## Run

The React frontend is in [frontend/](frontend/). Start the FastAPI backend using [app/README.md](app/README.md), then run `npm install` and `npm run dev` from `frontend/`. The frontend proxies API requests to `http://127.0.0.1:8000` by default; see [frontend/README.md](frontend/README.md) for setup and current API limitations.

This remains a prototype: use synthetic data only. The local agent/MCP workflow and one-command full-stack seeded start are not implemented yet.

## Privacy and safety

Do not put real patient information in issues, commits, prompts, demo recordings or third-party tools. Use synthetic data until the facility approves the workflow, hosting, privacy controls and clinical protocol. Clinician approval must be authenticated and auditable.

See [DATA_AND_PRIVACY.md](DATA_AND_PRIVACY.md) for the detailed data inventory, privacy rules, security controls, retention and pilot governance.

## Licence

See [LICENSE](LICENSE).
