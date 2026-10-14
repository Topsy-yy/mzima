import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.domain import RoleEnum, VisitStatusEnum


# --- Walk-in Schemas ---
class VisitCreate(BaseModel):
    age_band: str = Field(..., description="'under_5', 'adult', or 'over_65'")
    visit_type: str = Field(..., description="'new', 'review', or 'refill'")
    red_flags: dict[str, bool] = Field(default_factory=dict)


class VisitResponse(BaseModel):
    id: uuid.UUID
    token_number: str
    arrival_time: datetime
    age_band: str
    visit_type: str
    is_fast_track: bool
    red_flags: dict
    status: VisitStatusEnum
    triage_start_time: datetime | None = None
    triage_end_time: datetime | None = None
    triage_category: str | None = None
    destination: str | None = None

    class Config:
        from_attributes = True


class QueueItemResponse(BaseModel):
    visit_id: uuid.UUID
    token_number: str
    arrival_time: datetime
    minutes_waiting: int
    is_fast_track: bool
    is_wait_capped: bool
    calculated_score: float
    red_flags: dict


class CallTokenRequest(BaseModel):
    override_reason: str | None = Field(
        None, description="Reason code if calling token out of score order"
    )


class TriageUpdate(BaseModel):
    triage_category: str = Field(..., description="SATS / TEWS / ETAT classification")
    destination: str = Field(
        ..., description="Emergency bay, Consultation, Fast stream, Lab, Pharmacy"
    )


# --- Appointment Schemas ---
class AppointmentRequestCreate(BaseModel):
    patient_identifier: str
    requested_specialty: str


class AppointmentRequestResponse(BaseModel):
    id: uuid.UUID
    patient_identifier: str
    requested_specialty: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClinicianDecisionCreate(BaseModel):
    decision: str = Field(..., description="'APPROVE', 'REJECT', or 'MODIFY'")
    reason: str | None = None


class ClinicianDecisionResponse(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    clinician_id: uuid.UUID
    decision: str
    reason: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True