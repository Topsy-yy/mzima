# Mzima | Appointment and Routing Co-pilot

Mzima is a prototype concept for helping patients request an early outpatient appointment and helping facility staff review where that appointment belongs. A locally hosted reasoning agent gathers structured information, checks slots and facility-approved routing guidance, and proposes a sector and priority. A named clinician must approve, edit, or reject any proposal before it can affect a booking or queue position.

**Safety boundary:** Mzima is not a diagnostic system and does not autonomously triage, refer, raise deterioration flags, or change queue position. The five-day prototype is for synthetic cases and a simulated single-facility workflow. It is not for live care.

## What makes it an agent

The agent plans a bounded workflow, calls reusable MCP tools, validates tool results, asks follow-up questions when needed, retries safe reads, and hands off when uncertain. Its own MCP server has three tools: read appointment slots, score and save a pending route proposal, and commit a clinician-approved decision. Tool inputs, outputs, timestamps and approval identity are logged.

The full task runs on an open-weight model hosted in-country. Patient data must not leave the country. Any frontier-model comparison uses synthetic data only. ElevenLabs is limited to generic, non-personal audio unless an in-country deployment and data handling are verified; patient speech and personalized appointment details stay local.

## Project status

The repository includes a synthetic appointment workflow: a deterministic slot tool proposes the earliest matching available slot, and only an authenticated clinician approval reserves it. No-match and stale-capacity cases fail closed. This is not a model-driven agent and `app/mcp/appointment_tools.py` is an internal tool module, not a standards-compliant MCP server. Model orchestration, MCP transport/authentication, facility routing guidance, and model-based evaluation remain unimplemented.

## Intended sub-theme and workflow

**Sub-theme:** responsible agentic AI for access to care and outpatient operations.  
**Facility:** one participating outpatient facility; selection pending.  
**Workflow:** patient requests earliest appointment → local agent proposes a sector/priority → named clinician reviews → approved appointment enters the queue.

## Run

Follow [app/README.md](app/README.md) for the local synthetic setup, including migrations, randomly generated staff demo accounts, sample slots, the API, and the React frontend in [frontend/](frontend/). The frontend proxies API requests to `http://127.0.0.1:8000` by default; see [frontend/README.md](frontend/README.md) for current limitations.

This remains a prototype: use synthetic data only. It is not ready for live care or deployment. Run `python -m pytest -q` for deterministic workflow evaluations and `npm --prefix frontend run build` for the frontend production check. Model/MCP behavioral cases remain not run; see [EVALS.md](EVALS.md).

## Privacy and safety

Do not put real patient information in issues, commits, prompts, demo recordings or third-party tools. Use synthetic data until the facility approves the workflow, hosting, privacy controls and clinical protocol. Clinician approval must be authenticated and auditable.

See [DATA_AND_PRIVACY.md](DATA_AND_PRIVACY.md) for the detailed data inventory, privacy rules, security controls, retention and pilot governance.

## Licence

See [LICENSE](LICENSE).
