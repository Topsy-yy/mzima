# Mzima | Data, Privacy and Safety

**Status:** design requirements for a synthetic-data prototype. Mzima is not approved for live patient information or clinical use. The pilot facility, data controller and hosting environment have not yet been selected.

## Data to collect

Collect only what is needed to request, review and confirm an appointment. The facility must approve the final fields and purpose.

| Record | Prototype fields |
|---|---|
| Appointment request | Random request ID, patient-provided contact method if needed for confirmation, requested service, preferred times, age band only if facility rules require it, structured visit reason, language, created time and status |
| Agent proposal | Proposed sector/priority/concern flag, evidence fields used, uncertainty, rule/model version, proposal ID and time |
| Clinician decision | Authenticated clinician ID, approve/edit/reject, reason, before/after values and time |
| Appointment | Confirmed slot, facility sector, status, confirmation channel and delivery result |
| Operations | Slot capacity, staffing availability, system events, tool calls, retries and integration status |

Do not collect national ID, full date of birth, diagnosis, biometric/voiceprint, or audio by default. If the clinic needs identity matching or additional clinical context, document the necessity, authority, safeguards and retention before adding it. Free-text symptom descriptions and contact details are health-related personal data when linked to a person; minimize and restrict them accordingly.

## Where data may go

- The full patient workflow, model inference, database, logs, backups and support access must stay in Kenya, in line with this project requirement. Verify the actual location of all subprocessors and telemetry; “local model” alone does not guarantee local processing.
- Patient audio should be transcribed locally and discarded after confirmation unless the facility establishes a justified retention need. Personalized audio replies must be generated locally.
- ElevenLabs may only receive generic text with no patient details for a non-personal audio prompt, unless an approved in-country service and data path are verified.
- Frontier model comparisons, third-party MCPs, Zapier, analytics platforms and demo recordings use synthetic data only. Never send real patient data to them.
- Use a local mock clinic API for the prototype. For a real integration, share the minimum approved booking fields through the facility's documented interface. Do not assume an HMIS supports FHIR.

## Access and security controls

- Separate roles for patients, registration staff, clinicians, shift leads and administrators; give each only the access needed for their task.
- Authenticate clinic staff. Require a named clinician and recorded reason to approve/edit/reject a proposal. Do not treat an agent, API key or shared account as the approving clinician.
- Encrypt connections and stored data; protect keys and secrets; restrict database and MCP network access; use least-privilege accounts.
- Keep an append-only audit trail of reads and writes that affect a request or queue: actor, timestamp, tool/route, minimized input, output, status, before/after values, retries and clinician approval identity.
- Do not put sensitive data in ordinary application logs, URLs, analytics, crash reports, source control, screenshots or demo videos. Use request IDs and redaction.
- Back up locally with access controls and test restore. Define outage, incident response, breach escalation and secure deletion procedures with the facility.

## Retention and patient rights

The facility/data controller must set retention periods for unconfirmed requests, confirmed bookings, audit events, backups and derived data. Keep each only as long as its approved purpose and applicable records rules require; then securely delete or irreversibly de-identify it. Provide a way for staff to correct inaccurate data and process patient requests through the facility's established process.

## Safety and failure handling

- The agent can propose a concern flag, sector, priority or referral; it cannot make that decision effective without clinician approval.
- Every proposal shows the source facts and applicable facility rule. Missing facts, conflicting answers, no safe match, low confidence, stale appointment slots or model/tool errors trigger staff review.
- Agent failure must never erase a request or silently put it into a clinical priority. Keep the request visibly pending, alert staff, and allow manual/paper handling.
- A committed booking is idempotent. If an integration times out, check its result before retrying so duplicate appointments are not created.
- Monitor errors and overrides, and review whether outcomes differ across relevant groups. Do not use patient profiles to train or fine-tune models without a separate approved purpose and safeguards.

## Governance before real data

Before a live pilot, the facility and responsible data controller should confirm purpose and lawful basis, notices/consent requirements, controller/processor roles, security controls, retention, incident handling, hosting, any cross-border processing, ethics review and clinical ownership. Complete a data protection impact assessment where required and consult the facility's Data Protection Officer and clinical lead. This document is an engineering checklist, not legal advice.

Kenyan references: [Data Protection Act, 2019](https://new.kenyalaw.org/akn/ke/act/2019/24/eng%402022-12-31/source), [Digital Health Act, 2023](https://new.kenyalaw.org/akn/ke/act/2023/15/eng%402023-11-24/source), and [ODPC guidance notes](https://www.odpc.go.ke/guidelines-2/), including health data, consent and DPIA guidance.
