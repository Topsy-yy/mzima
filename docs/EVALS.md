# Mzima Evaluation Plan

**Status: automated checks added; execution not verified in this environment.** The current executable tests evaluate the deterministic synthetic slot workflow, not an LLM or MCP server. Do not report a PASS until `python -m pytest -q` completes successfully. No real patient data is used.

| # | Synthetic task | Required pass condition | Test / result |
|---|---|---|---|
| 1 | Matching synthetic request | Stores earliest matching available slot and pending proposal evidence; does not book before review | `test_patient_request_is_visible_only_in_authenticated_staff_inbox` / NOT RUN |
| 2 | Clinician approves or rejects | Approval reserves one slot; rejection does not book; decision requires a reason and cannot repeat | `test_clinician_decision_requires_reason_is_audited_and_cannot_repeat` / NOT RUN |
| 3 | No matching slot | Approval is rejected and request remains pending without a booking | `test_approval_fails_when_request_has_no_matching_slot` / NOT RUN |
| 4 | Two requests propose the last slot | First approval reserves capacity; second approval fails without overbooking | `test_stale_slot_proposal_cannot_overbook_capacity` / NOT RUN |
| 5 | Missing clinical detail / safety concern / unsupported routing | Current implementation has no clinical intake or routing model; these cases are not applicable yet | NOT IMPLEMENTED |
| 6 | Tool timeout, lost commit response, prompt injection, or data-egress attempt | Requires model orchestration and a standards-compliant MCP boundary | NOT IMPLEMENTED |

## Unfixed failure and next experiment

**Known gap:** automated workflow tests have been added but could not be run here, so there are no pass/fail results. The model/MCP recovery, injection, and data-egress evaluations remain unimplemented.  
**Next experiment:** run the four pytest cases and record their actual output. Then implement the selected local model and MCP transport behind explicit trust boundaries before evaluating model behavior; do not imply that deterministic rule tests validate a model.

## Reporting rules

- A task passes only if the expected outcome and all required audit fields are present.
- Any unauthorized queue-affecting write is an automatic FAIL.
- Report counts and traces, not just model self-assessment.
- Include one real unresolved failure, what was tried, risk, and the next experiment in the final version.
