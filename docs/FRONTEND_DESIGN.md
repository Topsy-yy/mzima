# Mzima Frontend Design

This document translates the repository's project goals, safety requirements, and team role split into a concrete frontend plan for Vee's ownership: the patient-facing appointment request flow and the clinician review experience.

## 1. Product intent

The frontend must feel trustworthy, calm, and clinically safe. It should support a patient requesting the earliest appointment, a local reasoning agent preparing a proposal, and a named clinician deciding whether to approve, edit, or reject it.

Key rules from the project documentation:

- The system is not a diagnostic tool and must never silently change queue priority.
- Patient data must stay minimal, local, and synthetic in the prototype.
- Clinician approval must be explicit, authenticated, and auditable.
- The UI must make agent decisions visible for demo review and staff oversight.
- The patient experience should be simple, not clinical, while the clinician experience must be evidence-rich and decision-focused.

## 2. Frontend scope

### Patient-facing experience
- Appointment request form
- Voice-assisted request flow
- Confirmation and waiting state
- Status screen after submission
- Staff handoff / manual review messaging

### Clinician experience
- Review queue for pending appointment requests
- Evidence panel for the agent proposal
- Approve / edit / reject actions
- Audit trail and request history
- Handoff state when the system cannot safely proceed

### Shared support surfaces
- Authentication and role-aware navigation
- Consent and safety notices
- Localization for Kenyan English and Kiswahili
- Demo mode with visible agent traces and tool outputs

## 3. Recommended frontend architecture

Use a lightweight modern web app built for a prototype environment, with a clean separation between patient and staff workflows:

- React + TypeScript + Vite for a fast, maintainable frontend shell
- State management via a small store or React Query/TanStack Query for API call lifecycle
- Router for patient and clinician flows
- Localized copy with `en-KE` and `sw-KE`
- Design system tuned for accessibility and clinic use
- No direct MCP access from browser; all calls go through the local REST API

This matches the intended architecture in the project docs: the patient and staff clients call Mzima's local API, while the reasoning agent and MCP tools remain server-side and bounded.

## 4. Design principles

### Safety-first UX
- Always communicate that the system is not diagnosing the patient.
- Do not present a proposed urgency as a confirmed outcome.
- Use explicit labels such as: Draft proposal, Pending clinician review, Approved, Rejected.
- Show the clinician review gate before any queue-affecting change.

### Minimal data collection
- Ask only for the fields needed for an appointment request and routing decision.
- Do not expose unnecessary personal detail in the interface.
- Mask and redact sensitive fields until a clinician opens a case.
- For demo mode, use synthetic patient records only.

### Trust and transparency
- Show the source facts behind every proposal.
- Highlight uncertainty, missing data, or staff handoff cases.
- Display the evidence panel on the clinician dashboard instead of hiding it in a modal.

### Inclusive access
- Support touch-friendly interactions for busy clinical staff.
- Ensure keyboard navigation and semantic form structure.
- Provide high contrast and large action buttons.
- Include both English and Kiswahili copy, with simple wording suited to low-literacy settings.

## 5. Patient app experience

### 5.1 Entry screen
A calm, one-page intake flow that starts with a short explanation:

- "Request an earlier appointment"
- "We help you ask for the most suitable clinic route"
- "A clinician reviews any proposed priority before it affects your queue position"

Microcopy should be reassuring and purpose-limited. The page should include:
- facility name or placeholder
- trusted language toggle
- progress indicator
- simple help text for wait time, service selection, and contact method

### 5.2 Request form
Fields should be minimized and structured:

Required or recommended fields:
- preferred service / appointment type
- visit reason in structured categories or short free text
- language preference
- contact method (phone / SMS / WhatsApp if needed)
- preferred time window
- age band only if the facility rule requires it

Form behavior:
- show validation only when a field is necessary
- ask one focused follow-up if the agent needs missing information
- allow spoken input through local STT when available
- support corrections before submission

### 5.3 Voice-assisted input
For demo use and local prototype deployment:

- microphone button on key input fields
- speech-to-text runs locally, never sends raw patient speech to a third-party service
- transcript is shown for review before submission
- user can edit the transcript before sending
- if the audio input is too unclear, switch to typed mode without losing progress

This is especially valuable for low-literacy or accessibility scenarios. It also aligns with the repository's requirement to keep speech local and to limit generic voice-only outputs to local or approved in-country pathways.

### 5.4 Review and confirmation screen
After submission:

- show a clear status banner: "Request received"
- tell the patient that the system is reviewing and that a clinician will approve any queue change
- display the request ID, status, and next step
- show summary of details entered
- avoid showing speculative urgency or diagnosis

### 5.5 Pending / handoff states
The patient should see one of these statuses:
- Pending review
- Additional information needed
- Awaiting clinician decision
- Staff handoff / manual follow-up required
- Confirmed appointment

The front-end should present staff handoff as a calm support flow, not a failure message.

## 6. Clinician dashboard UX

### 6.1 Review queue
The clinician dashboard should feel like a triage inbox, not a generic admin page.

Columns should include:
- request ID
- age band / service
- submitted time
- agent suggestion
- proposed priority / sector
- confidence or evidence count
- risk / concern flag
- status (pending, approved, rejected, needs clarification)

Action patterns:
- approve as proposed
- edit before approval
- reject with reason
- assign to manual staff follow-up

### 6.2 Proposal detail panel
When a request is selected, the interface should show:
- patient summary (minimized to only necessary context)
- structured reason for visit
- facility rules used
- agent rationale
- evidence fields and sources
- any missing data or uncertainty state
- rule version or model version if available

This panel should make the reasoning visible without exposing internal chain-of-thought or hidden system text. It must show source facts and decision points, not just an opaque recommendation.

### 6.3 Approval workflow
The approval form should require:
- named clinician identity
- approval action (approve / edit / reject)
- reason for decision
- before/after values when changed
- optional note for queue or service adjustments

UI states:
- Draft approval
- Ready to submit
- Submitted successfully
- Rejected and logged

Need robust confirmation to prevent accidental approval. The app should ask for clear intent before committing a queue-affecting decision.

### 6.4 Audit and trace visibility
A section should display the request lifecycle:
- request created
- agent read slots and rules
- proposal generated
- clinician reviewed
- approval or rejection timestamp
- final committed state

For demo purposes, this section should show tool call metadata in readable form: action, timestamp, correlation ID, result status, retry count. This aligns with the repository requirement for visible tool traces and audit integrity.

### 6.5 Staff handoff
When the agent is uncertain, cannot match a rule, or a tool fails, the clinician dashboard should surface a staff-handoff card:

- reason for handoff
- required human action
- no queue-affecting action taken automatically
- ability to continue manually

This is a critical UX requirement for safe operation and aligns with the system's design principles.

## 7. Information architecture

### Public / patient flows
- Home / request page
- Intake form
- Voice capture
- Review confirmation
- Status page

### Clinician flows
- Login
- Review queue
- Request detail review
- Decision form
- Audit trail panel
- Manual handoff or resolved case states

### Shared / system flows
- Authenticated role checks
- Local API loading states
- Error boundaries
- Safe fallback / offline prompts

## 8. State model for the frontend

Suggested front-end state progression:

- `idle`
- `collecting_details`
- `reviewing_input`
- `submitting_request`
- `awaiting_agent_review`
- `pending_clinician_decision`
- `approved`
- `rejected`
- `needs_follow_up`
- `manual_staff_handoff`

This mirrors the project's agent workflow and makes the UI more understandable for staff and demo recording.

## 9. Accessibility and localization

### Accessibility
- Color-coded status chips with text labels, not color alone
- Large buttons and spacing for staff tablets or desktops
- Screen-reader friendly forms and tables
- Keyboard shortcuts for common approval actions
- High contrast for status severity and safety notes

### Language support
The frontend should support:
- Kenyan English (`en-KE`)
- Kiswahili (`sw-KE`)

Copy should favor plain, direct wording and avoid jargon. Examples:
- "Request received"
- "Clinician review pending"
- "Awaiting appointment decision"
- "Handoff to staff"

### Data minimization in the UI
- Use short summaries and tags instead of long free text on queue pages
- Expand to full details only when a clinician opens the request
- Hide full contact information behind a secure view or masked display
- Never put real patient data into screenshots or demo recordings unless synthetic data is explicitly used

## 10. Demo-supporting UI design

Because the project explicitly calls for demo recording support, the interface should expose the internal decision path in a way that is both helpful and safe:

- visible status timeline with timestamps
- evidence card showing why the proposal was made
- tool trace panel with minimal metadata and outcomes
- named clinician identity when a decision is made
- annotated audit trail showing approve / reject / edit decisions

This allows the demo to narrate the agent's workflow without turning the UI into a technical debug console.

## 11. Frontend interaction examples

### Example: patient submission flow
1. Patient enters visit reason and preferred time.
2. App uses local voice input if available.
3. System validates required fields.
4. Request is submitted to `POST /api/appointment-requests`.
5. Patient sees a confirmation that the request is pending review.
6. Agent later proposes an urgency or routing suggestion.
7. Clinician reviews and approves or edits it.

### Example: clinician review flow
1. Clinician opens the review queue.
2. Queue shows pending requests sorted by urgency and time.
3. Clinician opens one case.
4. Evidence panel shows rule version, relevant fields, and uncertainty.
5. Clinician chooses approve, edit, or reject.
6. App submits to `POST /api/appointment-requests/{id}/decision`.
7. Request updates to `approved`, `rejected`, or `needs_clarification`.

## 12. Recommended screen list

### Patient app
- Landing / request home
- Request form
- Voice capture modal
- Review and submit screen
- Request status page
- Staff handoff message page

### Clinician app
- Login screen
- Review inbox
- Request detail / evidence screen
- Decision form
- Audit trail panel
- Manual handoff / unresolved case view

## 13. Risk-aware UX requirements

The interface must actively protect clinical safety:

- never label a proposal as final without clinician approval
- show risk or uncertainty clearly before any action is taken
- block automatic queue changes unless the clinician has explicitly approved them
- surface a handoff path rather than forcing a decision when evidence is weak
- ensure approved actions are logged with clinician identity and reason

## 14. Design recommendation for Vee

Vee's role is not only to make the interface look good; it must also make the workflow feel safe, legible, and accountable. The frontend should be designed like a clinic operational tool:

- patient-facing sections should be calm and respectful
- clinician tools should be direct and evidence-based
- the queue should reinforce clinical ownership in every action
- the audit and tool-trace experience should help staff trust the protocol, not merely the UI

This is the right balance for the Mzima prototype: a polished patient experience, a credible clinical decision surface, and a clear safety boundary between patient input, agent reasoning, and clinician authority.
