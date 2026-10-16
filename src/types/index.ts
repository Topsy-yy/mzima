export type ApiRole = 'clerk' | 'nurse' | 'shift_lead' | 'admin';

export interface ApiUser { id: string; username: string; role: ApiRole; }

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

export interface QueueItem {
  visit_id: string;
  token_number: string;
  arrival_time: string;
  minutes_waiting: number;
  is_fast_track: boolean;
  is_wait_capped: boolean;
  calculated_score: number;
  red_flags: Record<string, boolean>;
}

export interface AppointmentRequest {
  id: string;
  patient_identifier: string;
  requested_specialty: string;
  status: string;
  created_at: string;
}

export interface ClinicianDecision {
  id: string;
  request_id: string;
  clinician_id: string;
  decision: string;
  reason: string | null;
  created_at: string;
}