# Mzima frontend

React + TypeScript frontend for the local Mzima API prototype. The interface has a public landing page, guided patient appointment-request chat, staff walk-in queue/front desk, and authenticated clinician review inbox.

## Start locally

1. Start the API from the repository root using the setup in [../app/README.md](../app/README.md). The API should be available at `http://127.0.0.1:8000`.
2. In this directory, run `npm install` once, then `npm run dev`.
3. Open `http://localhost:5173`.

The Vite development server proxies `/api`, `/health`, and `/ready` to `http://127.0.0.1:8000`. Set `MZIMA_API_URL` if the backend listens elsewhere.

## API wiring and current limits

The frontend calls the implemented `/api/v1` routes for staff login, appointment-request submission and review, walk-in queue retrieval, check-in, call, and staff triage-record updates. Staff access tokens are held in session storage and sent as bearer tokens. Server-side role checks remain authoritative.

The patient flow accepts only `patient_identifier` and `requested_specialty`, uses synthetic references, previews before sending, and displays the API receipt. It is a guided UI, not a live AI chat service. The clinician inbox displays deterministic slot evidence and allows a shift lead/admin to reject or approve and book the proposed slot. No diagnosis or clinical priority is generated. The interface is English-only; voice input, model proposals, request history, and booking notifications are not implemented. Clinicians cannot edit a proposal because no edit contract exists.

Walk-in endpoints are the existing prototype queue workflow, separate from the planned agentic appointment-routing workflow. This interface is for synthetic data and is not for live care.

## Build

Run `npm run build` to type-check and create the production bundle in `dist/`.
