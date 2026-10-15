from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PatientInput(BaseModel):
    """Raw patient request captured at intake."""

    chief_complaint: str = Field(
        ...,
        description="Patients main reason for visit"
    )
    age_band: str = Field(
        ...,
        description='under_5 adult or over_65'
    )
    visit_type: str = Field(
        ...,
        description='new review or refill'
    )
    preferred_specialty: Optional[str] = Field(
        None,
        description="Patient requested specialty if any"
    )
    urgency: Optional[str] = Field(
        None,
        description='routine urgent or emergency'
    )

    model_config = ConfigDict(json_schema_extra={"example": {
        "chief_complaint": "Fever and cough for 3 days",
        "age_band": "adult",
        "visit_type": "new",
        "preferred_specialty": "general",
        "urgency": "routine",
    }})


class AppointmentSlots(BaseModel):
    """Available appointment slots returned from MCP get_appointment_slots."""

    facility_id: str = Field(
        ...,
        description="Facility identifier"
    )
    service_id: str = Field(
        ...,
        description="Service slot identifier"
    )
    start_time: datetime = Field(
        ...,
        description="Slot start time (UTC)"
    )
    end_time: datetime = Field(
        ...,
        description="Slot end time (UTC)"
    )
    capacity: int = Field(
        default=0,
        description="Number of slots available"
    )
    booked: int = Field(
        default=0,
        description="Number of slots already booked"
    )
    sector: str = Field(
        ...,
        description="Routing sector general pediatrics"
    )
    priority: str = Field(
        default="normal",
        description="Priority level normal high urgent"
    )

    model_config = ConfigDict(json_schema_extra={"example": {
        "facility_id": "facility-01",
        "service_id": "slot-123",
        "start_time": "2025-01-15T09:00:00Z",
        "end_time": "2025-01-15T09:30:00Z",
        "capacity": 5,
        "booked": 2,
        "sector": "general",
        "priority": "normal",
    }})


class ProposedRoute(BaseModel):
    """Output of score_and_propose_route a pending proposal."""

    request_id: str = Field(
        ...,
        description="UUID of the appointment request"
    )
    sector: str = Field(
        ...,
        description="Approved routing sector"
    )
    priority: str = Field(
        default="normal",
        description="Priority level"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence in this proposal (0-1)"
    )
    evidence: Dict[str, object] = Field(
        ...,
        description="Which fields rules drove the decision"
    )
    uncertainty_flag: bool = Field(
        default=False,
        description="True when model cannot confidently assign sector priority"
    )
    rule_version: str = Field(
        ...,
        description="Version of the rule file used for scoring"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the proposal was created"
    )

    model_config = ConfigDict(json_schema_extra={"example": {
        "request_id": "req-abc123",
        "sector": "general",
        "priority": "normal",
        "confidence": 0.87,
        "evidence": {"age_band": "adult", "urgency": "routine"},
        "uncertainty_flag": False,
        "rule_version": "v2025.1",
    }})


class ClinicianDecision(BaseModel):
    """Decision recorded by the authenticated clinician."""

    decision: str = Field(
        ...,
        description="APPROVE REJECT or MODIFY"
    )
    reason: Optional[str] = Field(
        None,
        description="Free-text reason from the clinician"
    )
    approved_sector: Optional[str] = Field(
        None,
        description="If MODIFY the sector the clinician chose"
    )
    approved_priority: Optional[str] = Field(
        None,
        description="If MODIFY the priority the clinician chose"
    )
    proposal_id: str = Field(
        ...,
        description="ID of the proposal being acted on"
    )
    clinician_id: str = Field(
        ...,
        description="Identifier of the approving clinician"
    )
    approved_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the decision was recorded"
    )

    model_config = ConfigDict(json_schema_extra={"example": {
        "decision": "APPROVE",
        "reason": "Clinician reviewed and approved",
        "approved_sector": None,
        "approved_priority": None,
        "proposal_id": "prop-xyz789",
        "clinician_id": "clinician-01",
        "approved_at": "2025-01-15T10:15:00Z",
    }})


class AuditRecord(BaseModel):
    """Minimised audit entry for a tool call or agent step."""

    correlation_id: str = Field(
        ...,
        description="Unique ID linking all steps of one request"
    )
    actor: str = Field(
        description="Who what triggered the action e.g. agent clinician-01"
    )
    tool: Optional[str] = Field(
        None,
        description="Tool name if applicable e.g. get_appointment_slots"
    )
    status: str = Field(
        ...,
        description="ok error timeout retry"
    )
    input_summary: Dict[str, object] = Field(
        ...,
        description="Minimised input payload no raw PHI"
    )
    output_summary: Dict[str, object] = Field(
        ...,
        description="Minimised output payload no raw PHI"
    )
    retry_count: int = Field(
        default=0,
        description="How many retries were attempted"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the action occurred"
    )

    model_config = ConfigDict(json_schema_extra={"example": {
        "correlation_id": "corr-12345",
        "actor": "agent",
        "tool": "get_appointment_slots",
        "status": "ok",
        "input_summary": {"chief_complaint": "Fever and cough"},
        "output_summary": {"slots": 3, "sector": "general"},
        "retry_count": 0,
        "timestamp": "2025-01-15T09:02:00Z",
    }})


class RecoveryState(BaseModel):
    """State used when the agent needs to recover handoff."""

    reason: str = Field(
        ...,
        description="Why recoveryhandoff is needed"
    )
    last_successful_step: str = Field(
        ...,
        description="Last step that completed successfully"
    )
    stalled_slot_ids: List[str] = Field(
        default_factory=list,
        description="Slot IDs that were stale or unavailable"
    )
    pending_proposal_id: Optional[str] = Field(
        None,
        description="Proposal ID if a proposal was in-flight"
    )
    handoff_message: str = Field(
        ...,
        description="Human-readable message for staff"
    )

    model_config = ConfigDict(json_schema_extra={"example": {
        "reason": "Slot lookup exhausted max retries",
        "last_successful_step": "intake",
        "stalled_slot_ids": ["slot-123"],
        "pending_proposal_id": None,
        "handoff_message": "Could not find available slots please manual schedule",
    }})


class TaskState(BaseModel):
    """Typed task state for the Mzima LangGraph agent."""

    model_config = ConfigDict(
        json_schema_extra={"description": "Typed task state carried by LangGraph through intake slot lookup guidance lookup proposal clinician review commit verify"}
    )

    patient_input: PatientInput = Field(
        ...,
        description="Validated and structured patient request"
    )

    slots: List[AppointmentSlots] = Field(
        default_factory=list,
        description="Available slots from MCP may be empty if lookup failed"
    )
    slot_lookup_status: str = Field(
        default="pending",
        description="Status of the slot lookup pending ok error timeout"
    )
    slot_lookup_audit: Optional[AuditRecord] = Field(
        None,
        description="Audit record for the slot lookup tool call"
    )

    routing_guidance: Optional[Dict[str, object]] = Field(
        None,
        description="Facility-approved routing rules read from PostgreSQL MCP"
    )
    guidance_lookup_audit: Optional[AuditRecord] = Field(
        None,
        description="Audit record for the guidance lookup tool call"
    )

    proposal: Optional[ProposedRoute] = Field(
        None,
        description="Pending proposal from score_and_propose_route"
    )
    proposal_audit: Optional[AuditRecord] = Field(
        None,
        description="Audit record for the proposal tool call"
    )

    clinician_decision: Optional[ClinicianDecision] = Field(
        None,
        description="Decision recorded by the authenticated clinician"
    )
    clinician_decision_audit: Optional[AuditRecord] = Field(
        None,
        description="Audit record for the clinician decision"
    )

    commit_status: str = Field(
        default="pending",
        description="Status of the commit pending ok idempotent failed"
    )
    commit_audit: Optional[AuditRecord] = Field(
        None,
        description="Audit record for the review_and_commit tool call"
    )
    recovery: Optional[RecoveryState] = Field(
        None,
        description="Recoveryhandoff state if the workflow diverged"
    )

    correlation_id: str = Field(
        ...,
        description="Unique ID linking all steps of one patient request"
    )
    request_id: str = Field(
        default_factory=lambda: "",
        description="UUID of the appointment request DB record populated after create"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the task state was first created"
    )
    completed: bool = Field(
        default=False,
        description="True when the workflow has reached a terminal state"
    )

    @property
    def is_terminal(self) -> bool:
        """True if the workflow has completed or been handed off."""
        return self.completed or self.recovery is not None

    @property
    def last_audit(self) -> Optional[AuditRecord]:
        """Most recent audit record if any."""
        records = [
            x
            for x in [
                self.slot_lookup_audit,
                self.guidance_lookup_audit,
                self.proposal_audit,
                self.clinician_decision_audit,
                self.commit_audit,
            ]
            if x is not None
        ]
        return records[-1] if records else None

    @property
    def last_tool_name(self) -> Optional[str]:
        """Name of the last tool that was called if any."""
        if (audit := self.last_audit) is not None:
            return audit.tool
        return None
