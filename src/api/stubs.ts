// Stub adapters for screens that the backend does not yet support.
// Each entry names the endpoint that would be required.

// TODO: GET /api/v1/visits - list visits (README lists it; backend has no handler).
export async function listVisitsStub(): Promise<never[]> { return []; }

// TODO: flagged care-coordination visits endpoint.
export async function listFlaggedVisitsStub(): Promise<never[]> { return []; }

// TODO: decision log for a shift lead.
export async function listDecisionLogStub(): Promise<never[]> { return []; }

// TODO: appointment proposal enrichment (proposed slot, agent output, review checklist) beyond AppointmentRequestResponse.
export const appointmentProposalExtrasStub = { reason: 'Not provided by API', agentOutput: 'Not provided by API' };