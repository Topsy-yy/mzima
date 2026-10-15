"""Seed and refresh reference data for the Mzima flow-optimisation prototype."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain import Visit, VisitStatusEnum
from app.models.flow import (
    AssessmentStation,
    ClinicalReviewAlert,
    ClinicalRule,
    OperationalThresholdSet,
    PatientObservationSet,
    StaffingShift,
    TriageSourceDocument,
)
from app.services.flow.clinical_alerts import create_clinical_alerts
from app.services.flow.source_ingestion import ingest_triage_sources


def seed_triage_source_refs(db: Session, pdf_dir: str) -> None:
    ingest_triage_sources(db, pdf_dir)


def seed_clinical_rules(db: Session) -> None:
    source_doc = db.query(TriageSourceDocument).filter(TriageSourceDocument.title == "Interagency Integrated Triage Tool: Reference Card").first()
    base_source = "WHO/MSF/ICRC Interagency Integrated Triage Tool (reference card and age-specific tools)"
    rules: list[dict[str, Any]] = [
        {
            "rule_id": "iitt_airway_breathing_distress",
            "name": "Airway or breathing distress warning sign",
            "criteria": {"symptom_keywords": ["difficulty breathing", "shortness of breath", "stridor", "cyanosis", "grunting", "chest indrawing", "nasal flaring", "wheezing"], "oxygen_saturation_below": 92},
            "severity": "high",
        },
        {
            "rule_id": "iitt_red_sign_symptom",
            "name": "IITT red-sign symptom or exposure",
            "criteria": {"symptom_keywords": ["unresponsive", "convulsion", "seizure", "heavy bleeding", "haemorrhage", "hemorrhage", "poisoning", "ingestion", "chemical exposure", "snake bite", "threatened limb"]},
            "severity": "critical",
        },
        {
            "rule_id": "iitt_high_risk_vital_sign_hr",
            "name": "High-risk heart rate",
            "criteria": {"adult_heart_rate_outside": [50, 150], "under_5_heart_rate_outside": [90, 180]},
            "severity": "high",
        },
        {
            "rule_id": "iitt_capillary_refill_prolonged",
            "name": "Prolonged capillary refill",
            "criteria": {"capillary_refill_seconds_greater_than": 3},
            "severity": "high",
        },
        {
            "rule_id": "iitt_altered_mental_status",
            "name": "Altered mental status or unresponsiveness",
            "criteria": {"avpu_not_alert": True, "symptom_keywords": ["agitated", "confused", "lethargy", "unresponsive"]},
            "severity": "critical",
        },
        {
            "rule_id": "iitt_severe_pallor",
            "name": "Severe pallor",
            "criteria": {"severe_pallor": True},
            "severity": "medium",
        },
        {
            "rule_id": "iitt_high_risk_temperature",
            "name": "High-risk temperature",
            "criteria": {"temperature_outside_celsius": [36, 39]},
            "severity": "medium",
        },
        {
            "rule_id": "iitt_high_risk_respiratory_rate",
            "name": "High-risk respiratory rate",
            "criteria": {"age_specific_respiratory_rate": True},
            "severity": "high",
        },
    ]
    for item in rules:
        existing = db.query(ClinicalRule).filter(ClinicalRule.rule_id == item["rule_id"]).first()
        if existing:
            continue
        db.add(
            ClinicalRule(
                rule_id=item["rule_id"],
                name=item["name"],
                version="iitt-2023-reference-v1",
                category="warning_sign",
                source_document_id=source_doc.id if source_doc else None,
                source_reference=base_source,
                applicability={"age_bands": ["under_5", "adult", "over_65"], "uses_synthetic_observations_only": True},
                criteria=item["criteria"],
                evidence_template="Flagged because: {evidence}",
                severity=item["severity"],
                required_reviewer_role="nurse",
                approved_for_clinical_use=False,
                active=True,
            )
        )
    db.commit()


def seed_thresholds(db: Session) -> None:
    name = "default-flow-thresholds"
    if db.query(OperationalThresholdSet).filter(OperationalThresholdSet.name == name).first():
        return
    db.add(
        OperationalThresholdSet(
            name=name,
            version="v1",
            service_point=None,
            max_wait_for_triage_minutes=30,
            max_wait_for_assessment_minutes=60,
            utilisation_warning_threshold=0.85,
            utilisation_critical_threshold=1.0,
            queue_growth_warning_threshold=3,
            approved=False,
        )
    )
    db.commit()


def seed_stations(db: Session) -> None:
    if db.query(AssessmentStation).count() > 0:
        return
    stations = [
        ("ST-1", "Assessment Station 1", "main_outpatient", "zone_a", True, True, 4),
        ("ST-2", "Assessment Station 2", "main_outpatient", "zone_a", True, True, 4),
        ("ST-3", "Assessment Station 3", "main_outpatient", "zone_b", True, False, 4),
    ]
    for code, name, point, zone, functional, staffed, capacity in stations:
        db.add(
            AssessmentStation(
                station_code=code,
                name=name,
                service_point=point,
                zone_code=zone,
                functional=functional,
                staffed=staffed,
                capacity_per_hour=capacity,
                required_role="nurse",
                active=True,
            )
        )
    db.commit()


def seed_staffing(db: Session) -> None:
    if db.query(StaffingShift).count() > 0:
        return
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    shifts = [
        ("nurse", "main_outpatient", 3, 2),
        ("clinician", "main_outpatient", 1, 1),
        ("clerk", "main_outpatient", 1, 1),
    ]
    for role, point, planned, available in shifts:
        db.add(
            StaffingShift(
                shift_start=now - timedelta(hours=1),
                shift_end=now + timedelta(hours=7),
                role=role,
                service_point=point,
                planned_count=planned,
                available_count=available,
                notes="Synthetic prototype staffing",
            )
        )
    db.commit()


def seed_synthetic_observations(db: Session, rng: random.Random | None = None) -> int:
    rng = rng or random.Random(42)
    from uuid import uuid4
    from app.services.flow.clinical_alerts import evaluate_iitt_warning_signs
    from app.models.domain import Visit

    visits = db.query(Visit).all()
    visits_without_obs = []
    for visit in visits:
        if db.query(PatientObservationSet).filter(PatientObservationSet.visit_id == visit.id).first():
            continue
        visits_without_obs.append(visit)

    symptoms_for_fast_track = [
        "Difficulty breathing and chest tightness",
        "Fever 39 C with cough and fast breathing",
        "Severe headache, confused and vomiting",
        "Heavy bleeding after injury",
        "Snake bite to ankle",
    ]
    normal_symptoms = [
        "Follow-up review for chronic medication",
        "Mild cough for three days",
        "Routine antenatal check",
        "Minor sprain",
        "Refill request",
    ]

    obs_mappings = []
    alert_mappings = []
    created = 0
    for visit in visits_without_obs:
        is_fast = bool(visit.is_fast_track) or bool(visit.red_flags and any(visit.red_flags.values()))
        symptom = rng.choice(symptoms_for_fast_track if is_fast else normal_symptoms)
        obs_id = uuid4()
        obs_data = {
            "id": obs_id,
            "visit_id": visit.id,
            "temperature_c": rng.choice([36.1, 37.0, 37.8, 38.7, 39.1]) if is_fast else rng.choice([36.0, 36.6, 37.1]),
            "pulse_bpm": rng.choice([72, 88, 104, 126, 152]) if is_fast else rng.choice([68, 76, 84]),
            "respiratory_rate": rng.choice([18, 24, 28, 36, 44]) if is_fast else rng.choice([16, 18, 20]),
            "oxygen_saturation": rng.choice([88, 91, 94, 97]) if is_fast else rng.choice([95, 97, 99]),
            "capillary_refill_seconds": rng.choice([1.0, 2.0, 3.5, 4.0]) if is_fast else rng.choice([1.0, 1.5, 2.0]),
            "systolic_bp": rng.choice([100, 118, 132, 150]) if is_fast else rng.choice([105, 112, 120]),
            "diastolic_bp": rng.choice([62, 74, 86, 96]) if is_fast else rng.choice([65, 70, 78]),
            "avpu": rng.choice(["A", "V", "P"]) if is_fast else "A",
            "severe_pallor": rng.random() < 0.3 if is_fast else False,
            "reported_symptoms": symptom,
            "symptom_summary": {"source": "synthetic", "fast_track": is_fast},
            "data_source": "synthetic",
            "generator_name": "mzima-synthetic-seed",
            "generator_version": "v1",
            "collected_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "red_flag_rules_triggered": [],
        }
        obs_mappings.append(obs_data)
        # Build a lightweight observation object for rule evaluation.
        class _Obs:
            pass
        obs_obj = _Obs()
        for key, value in obs_data.items():
            setattr(obs_obj, key, value)
        obs_obj.id = obs_id
        visit.service_point = visit.service_point or "main_outpatient"
        for spec in evaluate_iitt_warning_signs(obs_obj, visit):
            alert_mappings.append(
                {
                    "id": uuid4(),
                    "visit_id": visit.id,
                    "observation_set_id": obs_id,
                    "rule_id": str(spec["rule_id"]),
                    "rule_version": str(spec["rule_version"]),
                    "severity": str(spec["severity"]),
                    "trigger_evidence": dict(spec["trigger_evidence"]),
                    "source_observation": dict(spec["source_observation"]),
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                }
            )
        created += 1

    if obs_mappings:
        db.bulk_insert_mappings(PatientObservationSet, obs_mappings)
    if alert_mappings:
        db.bulk_insert_mappings(ClinicalReviewAlert, alert_mappings)
    db.commit()
    return created


def seed_recent_activity(db: Session, rng: random.Random | None = None) -> int:
    rng = rng or random.Random(7)
    now = datetime.utcnow()
    visits = db.query(Visit).order_by(Visit.arrival_time.desc()).limit(120).all()
    if not visits:
        return 0
    updated = 0
    for visit in visits[:45]:
        arrival = now - timedelta(minutes=rng.randint(0, 110))
        visit.arrival_time = arrival
        visit.service_point = visit.service_point or "main_outpatient"
        if rng.random() < 0.45:
            visit.status = VisitStatusEnum.IN_QUEUE
            visit.triage_start_time = None
            visit.triage_end_time = None
            visit.first_assessment_start_time = None
            visit.first_assessment_end_time = None
        elif rng.random() < 0.3:
            visit.status = VisitStatusEnum.CALLED
            visit.triage_start_time = arrival + timedelta(minutes=rng.randint(3, 20))
            visit.triage_end_time = None
        elif rng.random() < 0.8:
            visit.status = VisitStatusEnum.TRIAGED
            visit.triage_start_time = arrival + timedelta(minutes=rng.randint(3, 20))
            visit.triage_end_time = visit.triage_start_time + timedelta(minutes=rng.randint(5, 15))
            visit.first_assessment_start_time = None
        else:
            visit.status = VisitStatusEnum.TRIAGED
            visit.triage_start_time = arrival + timedelta(minutes=rng.randint(3, 20))
            visit.triage_end_time = visit.triage_start_time + timedelta(minutes=rng.randint(5, 15))
            visit.first_assessment_start_time = visit.triage_end_time + timedelta(minutes=rng.randint(2, 10))
        updated += 1
    db.commit()
    return updated


def ensure_flow_reference_data(db: Session, pdf_dir: str) -> dict[str, int]:
    seed_triage_source_refs(db, pdf_dir)
    seed_clinical_rules(db)
    seed_thresholds(db)
    seed_stations(db)
    seed_staffing(db)
    observations_created = seed_synthetic_observations(db)
    recent_activity_updated = seed_recent_activity(db)
    return {"observations_created": observations_created, "recent_activity_updated": recent_activity_updated}

