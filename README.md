# Mzima | Appointment and Routing Co-pilot

Mzima is a prototype concept for helping patients request an early outpatient appointment and helping facility staff review where that appointment belongs. A locally hosted reasoning agent gathers structured information, checks slots and facility-approved routing guidance, and proposes a sector and priority. A named clinician must approve, edit, or reject any proposal before it can affect a booking or queue position.

**Safety boundary:** Mzima is not a diagnostic system and does not autonomously triage, refer, raise deterioration flags, or change queue position. The five-day prototype is for synthetic cases and a simulated single-facility workflow. It is not for live care.

## What makes it an agent

The agent plans a bounded workflow, calls reusable MCP tools, validates tool results, asks follow-up questions when needed, retries safe reads, and hands off when uncertain. Its own MCP server has three tools: read appointment slots, score and save a pending route proposal, and commit a clinician-approved decision. Tool inputs, outputs, timestamps and approval identity are logged.

The full task runs on an open-weight model hosted in-country. Patient data must not leave the country. Any frontier-model comparison uses synthetic data only. ElevenLabs is limited to generic, non-personal audio unless an in-country deployment and data handling are verified; patient speech and personalized appointment details stay local.

## Project status

This repository is currently documentation only. There is no runnable application, MCP server, agent, public demo, or measured evaluation yet. The requirements and intended architecture are captured in [MZIMA_SYSTEM_DESIGN.md](MZIMA_SYSTEM_DESIGN.md) and [ARCHITECTURE.md](ARCHITECTURE.md). [EVALS.md](EVALS.md) is a test plan until an implementation produces real pass/fail results.

## Intended sub-theme and workflow

**Sub-theme:** responsible agentic AI for access to care and outpatient operations.  
**Facility:** one participating outpatient facility; selection pending.  
**Workflow:** patient requests earliest appointment → local agent proposes a sector/priority → named clinician reviews → approved appointment enters the queue.

## Run

There is no application to run yet. The submission-ready implementation must provide a one-command start with seeded synthetic data and local model instructions.

## Privacy and safety

Do not put real patient information in issues, commits, prompts, demo recordings or third-party tools. Use synthetic data until the facility approves the workflow, hosting, privacy controls and clinical protocol. Clinician approval must be authenticated and auditable.

See [DATA_AND_PRIVACY.md](DATA_AND_PRIVACY.md) for the detailed data inventory, privacy rules, security controls, retention and pilot governance.

## Licence

See [LICENSE](LICENSE).
