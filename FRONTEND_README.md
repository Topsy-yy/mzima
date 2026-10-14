# Mzima Frontend

React + TypeScript frontend for the local Mzima API prototype. The interface has a patient appointment-request page, a staff walk-in queue/front desk, and an authenticated clinician review inbox.

## Start locally

Follow the complete setup in the repository [README](../README.md), including PostgreSQL configuration and API startup. From the repository root, start the frontend in a second terminal:

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

Open `http://localhost:5173`. The Vite development server proxies `/api`, `/health`, and `/ready` to `http://127.0.0.1:8000`. Set `MZIMA_API_URL` in the frontend environment if the backend listens elsewhere.

## API wiring and current limits

The frontend calls the implemented `/api/v1` routes for staff login, appointment-request submission and review, walk-in queue retrieval, check-in, call, and staff triage-record updates. Staff access tokens are held in session storage and sent as bearer tokens. Server-side role checks remain authoritative.

The current appointment-request API accepts only `patient_identifier` and `requested_specialty`; the patient page therefore sends only those fields and directs prototype users to use synthetic references. The backend does not yet expose agent proposals/evidence, appointment slots, request history, or a booking confirmation endpoint. The clinician page explicitly presents this limitation rather than inventing clinical recommendations. The backend decision endpoint currently supports approve/reject behavior; this UI does not offer a modify action that the API cannot safely persist.

Walk-in endpoints are the existing prototype queue workflow, separate from the planned agentic appointment-routing workflow. This interface is for synthetic data and is not for live care.

## Build

Run `npm run build` to type-check and create the production bundle in `dist/`.
