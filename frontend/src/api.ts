export type ApiRole = 'clerk' | 'nurse' | 'shift_lead' | 'admin';

export interface ApiUser {
  id: string;
  username: string;
  role: ApiRole;
}

export interface AppointmentRequest {
  id: string;
  patient_identifier: string;
  requested_specialty: string;
  status: string;
  created_at: string;
  proposed_slot_id: string | null;
  booked_slot_id: string | null;
  agent_proposal: {
    tool?: string;
    status?: string;
    specialty?: string;
    slot_id?: string | null;
    starts_at?: string;
    evidence?: string[];
    rule_version?: string;
  } | null;
}

export interface QueueVisit {
  visit_id: string;
  token_number: string;
  arrival_time: string;
  minutes_waiting: number;
  is_fast_track: boolean;
  is_wait_capped: boolean;
  calculated_score: number;
  red_flags: Record<string, boolean>;
}

export interface Visit {
  id: string;
  token_number: string;
  arrival_time: string;
  age_band: string;
  visit_type: string;
  is_fast_track: boolean;
  red_flags: Record<string, boolean>;
  status: string;
  triage_start_time: string | null;
  triage_end_time: string | null;
  triage_category: string | null;
  destination: string | null;
}

export interface ClinicianDecision {
  id: string;
  request_id: string;
  clinician_id: string;
  decision: string;
  reason: string | null;
  created_at: string;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body instanceof URLSearchParams) {
    headers.set('Content-Type', 'application/x-www-form-urlencoded');
  } else if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      message = `Request failed (${response.status} ${response.statusText})`;
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function login(username: string, password: string): Promise<string> {
  const form = new URLSearchParams({ username, password });
  const result = await request<{ access_token: string }>('/api/v1/auth/login', {
    method: 'POST',
    body: form,
  });
  return result.access_token;
}

export function getCurrentUser(token: string): Promise<ApiUser> {
  return request('/api/v1/auth/me', {}, token);
}

export function getAppointmentQueue(token: string): Promise<AppointmentRequest[]> {
  return request('/api/v1/appointments/clinic/review-queue', {}, token);
}

export function createAppointmentRequest(
  patientIdentifier: string,
  specialty: string,
): Promise<AppointmentRequest> {
  return request('/api/v1/appointments/appointment-requests', {
    method: 'POST',
    body: JSON.stringify({
      patient_identifier: patientIdentifier,
      requested_specialty: specialty,
    }),
  });
}

export function decideAppointmentRequest(
  requestId: string,
  decision: 'APPROVE' | 'REJECT',
  reason: string,
  token: string,
): Promise<ClinicianDecision> {
  return request(
    `/api/v1/appointments/appointment-requests/${encodeURIComponent(requestId)}/decision`,
    {
      method: 'POST',
      body: JSON.stringify({ decision, reason }),
    },
    token,
  );
}

export function getWalkInQueue(token: string): Promise<QueueVisit[]> {
  return request('/api/v1/queue', {}, token);
}

export function checkInVisit(
  payload: {
    age_band: string;
    visit_type: string;
    red_flags: Record<string, boolean>;
  },
  token: string,
): Promise<Visit> {
  return request('/api/v1/visits', {
    method: 'POST',
    body: JSON.stringify(payload),
  }, token);
}

export function callVisit(
  visitId: string,
  overrideReason: string,
  token: string,
): Promise<Visit> {
  return request(
    `/api/v1/queue/${encodeURIComponent(visitId)}/call`,
    {
      method: 'POST',
      body: JSON.stringify({ override_reason: overrideReason || null }),
    },
    token,
  );
}

export function completeVisitTriage(
  visitId: string,
  triageCategory: string,
  destination: string,
  token: string,
): Promise<Visit> {
  return request(
    `/api/v1/visits/${encodeURIComponent(visitId)}/triage`,
    {
      method: 'POST',
      body: JSON.stringify({
        triage_category: triageCategory,
        destination,
      }),
    },
    token,
  );
}
