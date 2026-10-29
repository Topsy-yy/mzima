import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class RoleEnum(str, enum.Enum):
    CLERK = "clerk"
    NURSE = "nurse"
    SHIFT_LEAD = "shift_lead"
    ADMIN = "admin"


class VisitStatusEnum(str, enum.Enum):
    IN_QUEUE = "in_queue"
    CALLED = "called"
    TRIAGED = "triaged"
    LEFT_UNSEEN = "left_unseen"


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_number = Column(String(20), nullable=False, index=True)
    arrival_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    age_band = Column(String(20), nullable=False)  # e.g., 'under_5', 'adult', 'over_65'
    visit_type = Column(String(20), nullable=False)  # 'new', 'review', 'refill'
    
    # Door Screen Flags
    is_fast_track = Column(Boolean, default=False, index=True)
    red_flags = Column(JSON, default=dict)  # {"breathing_difficulty": true, ...}
    
    # Queue Lifecycle
    status = Column(Enum(VisitStatusEnum), default=VisitStatusEnum.IN_QUEUE, index=True)
    triage_start_time = Column(DateTime, nullable=True)
    triage_end_time = Column(DateTime, nullable=True)
    triage_category = Column(String(20), nullable=True)  # SATS/TEWS/ETAT
    destination = Column(String(50), nullable=True)  # Emergency, Consultation, Fast Stream, etc.

    events = relationship("QueueEvent", back_populates="visit")


class QueueEvent(Base):
    __tablename__ = "queue_events"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(Uuid(as_uuid=True), ForeignKey("visits.id"), nullable=False)
    actor_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # CALL, OVERRIDE, PROMOTION, FLAG_RAISED
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    reason_code = Column(String(100), nullable=True)

    visit = relationship("Visit", back_populates="events")


class AppointmentRequest(Base):
    __tablename__ = "appointment_requests"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_identifier = Column(String(100), nullable=False)
    requested_specialty = Column(String(100), nullable=False)
    status = Column(String(50), default="PENDING_REVIEW")  # PENDING_REVIEW, APPROVED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)
    proposed_slot_id = Column(Uuid(as_uuid=True), ForeignKey("appointment_slots.id"), nullable=True)
    booked_slot_id = Column(Uuid(as_uuid=True), ForeignKey("appointment_slots.id"), nullable=True)
    agent_proposal = Column(JSON, default=dict, nullable=False)

    decisions = relationship("ClinicianDecision", back_populates="request")


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialty = Column(String(100), nullable=False, index=True)
    starts_at = Column(DateTime, nullable=False, index=True)
    capacity = Column(Integer, nullable=False, default=1)
    booked_count = Column(Integer, nullable=False, default=0)


class ClinicianDecision(Base):
    __tablename__ = "clinician_decisions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(Uuid(as_uuid=True), ForeignKey("appointment_requests.id"), nullable=False)
    clinician_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision = Column(String(50), nullable=False)  # APPROVE, REJECT, MODIFY
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    request = relationship("AppointmentRequest", back_populates="decisions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    payload = Column(JSON, default=dict)