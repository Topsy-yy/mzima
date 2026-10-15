"""Flow-optimisation domain models for Mzima.

These models intentionally do not store diagnoses or make clinical decisions.
They record observations, capacity, alerts, recommendations, metrics, and simulations
that support deterministic operational analysis and evidence-backed staff review.
"""

from datetime import datetime
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class FlowAlertStatusEnum(str, str.__class__.Enum if False else object):
    pass


class AlertStatusEnum(str):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    RESOLVED = "resolved"


class RecommendationStatusEnum(str):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    APPLIED_EXTERNAL = "applied_external"


class ClinicalAlertSeverityEnum(str):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatientObservationSet(Base):
    __tablename__ = "patient_observation_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False, index=True)
    temperature_c = Column(Float, nullable=True)
    pulse_bpm = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    oxygen_saturation = Column(Integer, nullable=True)
    capillary_refill_seconds = Column(Float, nullable=True)
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    avpu = Column(String(10), nullable=True)
    severe_pallor = Column(Boolean, nullable=True)
    reported_symptoms = Column(Text, nullable=True)
    symptom_summary = Column(JSON, nullable=False, default=dict)
    data_source = Column(String(80), nullable=False, default="synthetic")
    generator_name = Column(String(120), nullable=True)
    generator_version = Column(String(80), nullable=True)
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    red_flag_rules_triggered = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    visit = relationship("Visit", backref="observation_sets")


class TriageSourceDocument(Base):
    __tablename__ = "triage_source_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    source_type = Column(String(80), nullable=False, default="clinical_protocol_reference")
    source_url = Column(String(500), nullable=True)
    license = Column(String(255), nullable=True)
    publisher = Column(String(255), nullable=True)
    published_date = Column(String(80), nullable=True)
    extracted_text = Column(Text, nullable=True)
    content_sha256 = Column(String(64), nullable=True)
    ingestion_status = Column(String(40), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ClinicalRule(Base):
    __tablename__ = "clinical_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(String(120), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(80), nullable=False, default="v1")
    category = Column(String(80), nullable=False, default="warning_sign")
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("triage_source_documents.id"), nullable=True)
    source_reference = Column(String(500), nullable=True)
    applicability = Column(JSON, nullable=False, default=dict)
    criteria = Column(JSON, nullable=False, default=dict)
    evidence_template = Column(Text, nullable=True)
    severity = Column(String(30), nullable=False, default="high")
    required_reviewer_role = Column(String(40), nullable=False, default="nurse")
    approved_for_clinical_use = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(120), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    source_document = relationship("TriageSourceDocument")


class ClinicalReviewAlert(Base):
    __tablename__ = "clinical_review_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False, index=True)
    observation_set_id = Column(UUID(as_uuid=True), ForeignKey("patient_observation_sets.id"), nullable=True)
    rule_id = Column(String(120), nullable=False, index=True)
    rule_version = Column(String(80), nullable=False)
    severity = Column(String(30), nullable=False, default="high")
    trigger_evidence = Column(JSON, nullable=False, default=dict)
    source_observation = Column(JSON, nullable=False, default=dict)
    status = Column(String(40), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    visit = relationship("Visit", backref="clinical_review_alerts")
    observation_set = relationship("PatientObservationSet")


class ClinicalReviewOutcome(Base):
    __tablename__ = "clinical_review_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("clinical_review_alerts.id"), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewer_role = Column(String(40), nullable=True)
    decision = Column(String(40), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    alert = relationship("ClinicalReviewAlert", backref="outcomes")
    reviewer = relationship("User")


class AssessmentStation(Base):
    __tablename__ = "assessment_stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_code = Column(String(80), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    service_point = Column(String(120), nullable=False, index=True)
    zone_code = Column(String(40), nullable=True)
    functional = Column(Boolean, nullable=False, default=True)
    staffed = Column(Boolean, nullable=False, default=True)
    capacity_per_hour = Column(Integer, nullable=False, default=4)
    required_role = Column(String(40), nullable=False, default="nurse")
    location_notes = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class StaffingShift(Base):
    __tablename__ = "staffing_shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shift_start = Column(DateTime, nullable=False, index=True)
    shift_end = Column(DateTime, nullable=False, index=True)
    role = Column(String(40), nullable=False, index=True)
    service_point = Column(String(120), nullable=True, index=True)
    planned_count = Column(Integer, nullable=False, default=0)
    available_count = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CapacitySnapshot(Base):
    __tablename__ = "capacity_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    service_point = Column(String(120), nullable=True, index=True)
    staff_available = Column(JSON, nullable=False, default=dict)
    stations_functional = Column(Integer, nullable=False, default=0)
    stations_staffed = Column(Integer, nullable=False, default=0)
    arrivals_last_hour = Column(Integer, nullable=False, default=0)
    completed_last_hour = Column(Integer, nullable=False, default=0)
    queue_length = Column(Integer, nullable=False, default=0)
    utilisation = Column(Float, nullable=False, default=0.0)
    capacity_gap = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class BottleneckAlert(Base):
    __tablename__ = "bottleneck_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_code = Column(String(120), nullable=False, index=True)
    service_point = Column(String(120), nullable=False, index=True)
    severity = Column(String(30), nullable=False, default="medium")
    metric_name = Column(String(80), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    evidence = Column(JSON, nullable=False, default=dict)
    threshold_set_version = Column(String(80), nullable=True)
    status = Column(String(40), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)

    acknowledger = relationship("User")


class OperationalRecommendation(Base):
    __tablename__ = "operational_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_type = Column(String(80), nullable=False)
    service_point = Column(String(120), nullable=False, index=True)
    suggested_action = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    projected_wait_reduction_minutes = Column(Float, nullable=True)
    projected_queue_reduction = Column(Integer, nullable=True)
    evidence = Column(JSON, nullable=False, default=dict)
    status = Column(String(40), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)

    reviewer = relationship("User")


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(120), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("simulation_scenarios.id"), nullable=False, index=True)
    baseline_metrics = Column(JSON, nullable=False, default=dict)
    scenario_metrics = Column(JSON, nullable=False, default=dict)
    assumptions = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    scenario = relationship("SimulationScenario", backref="results")


class PublicHealthContext(Base):
    __tablename__ = "public_health_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_name = Column(String(160), nullable=False)
    value = Column(String(120), nullable=False)
    unit = Column(String(80), nullable=True)
    geography = Column(String(160), nullable=False)
    publisher = Column(String(255), nullable=True)
    source_title = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=True)
    published_date = Column(String(80), nullable=True)
    citation = Column(Text, nullable=True)
    assumption_use = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class OperationalThresholdSet(Base):
    __tablename__ = "operational_threshold_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False, unique=True)
    version = Column(String(80), nullable=False, default="v1")
    service_point = Column(String(120), nullable=True)
    max_wait_for_triage_minutes = Column(Integer, nullable=False, default=30)
    max_wait_for_assessment_minutes = Column(Integer, nullable=False, default=60)
    utilisation_warning_threshold = Column(Float, nullable=False, default=0.85)
    utilisation_critical_threshold = Column(Float, nullable=False, default=1.0)
    queue_growth_warning_threshold = Column(Integer, nullable=False, default=3)
    approved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class FlowMetricSnapshot(Base):
    __tablename__ = "flow_metric_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    service_point = Column(String(120), nullable=True, index=True)
    assessment_station_id = Column(UUID(as_uuid=True), ForeignKey("assessment_stations.id"), nullable=True)
    queue_length = Column(Integer, nullable=False, default=0)
    arrivals = Column(Integer, nullable=False, default=0)
    completed = Column(Integer, nullable=False, default=0)
    avg_wait_for_triage_minutes = Column(Float, nullable=True)
    avg_wait_for_assessment_minutes = Column(Float, nullable=True)
    sla_breach_count = Column(Integer, nullable=False, default=0)
    utilisation = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    station = relationship("AssessmentStation")
