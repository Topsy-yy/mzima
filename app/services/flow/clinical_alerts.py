"""Deterministic clinical warning-sign evaluation.

This service applies facility-approved interagency triage references as warning signs only.
It never diagnoses, never assigns priority, and never changes queue position.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.domain import Visit
from app.models.flow import ClinicalReviewAlert, PatientObservationSet


def rule_context(obs: PatientObservationSet, visit: Visit) -> dict[str, object]:
    return {
        "temperature_c": obs.temperature_c,
        "pulse_bpm": obs.pulse_bpm,
        "respiratory_rate": obs.respiratory_rate,
        "oxygen_saturation": obs.oxygen_saturation,
        "capillary_refill_seconds": obs.capillary_refill_seconds,
        "systolic_bp": obs.systolic_bp,
        "diastolic_bp": obs.diastolic_bp,
        "avpu": obs.avpu,
        "severe_pallor": obs.severe_pallor,
        "reported_symptoms": obs.reported_symptoms or "",
        "symptom_summary": obs.symptom_summary or {},
        "age_band": visit.age_band,
        "visit_type": visit.visit_type,
        "visit_id": str(visit.id),
    }


def _contains_symptom(text: str, keywords: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return sorted({keyword for keyword in keywords if keyword in lowered})


def evaluate_iitt_warning_signs(obs: PatientObservationSet, visit: Visit) -> list[dict[str, object]]:
    """Return evidence-backed warning-sign alert specifications.

    The output intentionally contains evidence fields, not diagnoses.
    """
    specs: list[dict[str, object]] = []
    text = (obs.reported_symptoms or "").strip().lower()
    symptom_summary = obs.symptom_summary or {}

    # Reference: IITT adult/paediatric tool - respiratory distress / cyanosis / airway concern.
    respiratory_keywords = [
        "difficulty breathing",
        "shortness of breath",
        "breathless",
        "respiratory distress",
        "cyanosis",
        "stridor",
        "wheezing",
        "grunting",
        "chest indrawing",
        "nasal flaring",
    ]
    found_respiratory = _contains_symptom(text, respiratory_keywords)
    if found_respiratory or (obs.oxygen_saturation is not None and obs.oxygen_saturation < 92):
        evidence = {"reported_symptoms": obs.reported_symptoms}
        if found_respiratory:
            evidence["matched_keywords"] = found_respiratory
        if obs.oxygen_saturation is not None and obs.oxygen_saturation < 92:
            evidence["oxygen_saturation"] = obs.oxygen_saturation
            evidence["threshold"] = "SpO2 < 92%"
        specs.append(
            {
                "rule_id": "iitt_airway_breathing_distress",
                "rule_version": "iitt-2023-reference-card-v1",
                "severity": "high",
                "trigger_evidence": evidence,
                "source_observation": {
                    "reported_symptoms": obs.reported_symptoms,
                    "oxygen_saturation": obs.oxygen_saturation,
                },
            }
        )

    # Reference: IITT adult criteria - HR < 50 or > 150; paediatric thresholds handled as generic under-5 concern.
    if obs.pulse_bpm is not None:
        adult_hr_limit = obs.pulse_bpm < 50 or obs.pulse_bpm > 150
        pediatric_hr_limit = visit.age_band == "under_5" and (obs.pulse_bpm < 90 or obs.pulse_bpm > 180)
        if adult_hr_limit or pediatric_hr_limit:
            specs.append(
                {
                    "rule_id": "iitt_high_risk_vital_sign_hr",
                    "rule_version": "iitt-2023-reference-card-v1",
                    "severity": "high",
                    "trigger_evidence": {
                        "pulse_bpm": obs.pulse_bpm,
                        "age_band": visit.age_band,
                        "threshold": "adult <50 or >150; under_5 <90 or >180",
                    },
                    "source_observation": {
                        "pulse_bpm": obs.pulse_bpm,
                        "age_band": visit.age_band,
                    },
                }
            )

    if obs.capillary_refill_seconds is not None and obs.capillary_refill_seconds > 3:
        specs.append(
            {
                "rule_id": "iitt_capillary_refill_prolonged",
                "rule_version": "iitt-2023-reference-card-v1",
                "severity": "high",
                "trigger_evidence": {
                    "capillary_refill_seconds": obs.capillary_refill_seconds,
                    "threshold": "> 3 seconds",
                },
                "source_observation": {
                    "capillary_refill_seconds": obs.capillary_refill_seconds,
                },
            }
        )

    # Reference: IITT adult/paediatric - altered mental state / unresponsiveness / convulsions.
    if (obs.avpu and obs.avpu.upper() not in {"A", "ALERT"}) or symptom_summary.get("altered_mental_status"):
        specs.append(
            {
                "rule_id": "iitt_altered_mental_status",
                "rule_version": "iitt-2023-reference-card-v1",
                "severity": "critical",
                "trigger_evidence": {
                    "avpu": obs.avpu,
                    "reported_symptoms": obs.reported_symptoms,
                    "symptom_summary": symptom_summary,
                },
                "source_observation": {
                    "avpu": obs.avpu,
                    "reported_symptoms": obs.reported_symptoms,
                },
            }
        )

    # Reference: adult/paediatric IITT red signs and high-risk trauma/ingestion exposure.
    red_symptom_keywords = [
        "unresponsive",
        "convulsion",
        "seizure",
        "heavy bleeding",
        "haemorrhage",
        "hemorrhage",
        "poisoning",
        "ingestion",
        "chemical exposure",
        "snake bite",
        "threatened limb",
        "pregnant bleeding",
    ]
    matches = _contains_symptom(text, red_symptom_keywords)
    if matches:
        specs.append(
            {
                "rule_id": "iitt_red_sign_symptom",
                "rule_version": "iitt-2023-reference-card-v1",
                "severity": "critical",
                "trigger_evidence": {
                    "reported_symptoms": obs.reported_symptoms,
                    "matched_keywords": matches,
                },
                "source_observation": {
                    "reported_symptoms": obs.reported_symptoms,
                },
            }
        )

    if obs.severe_pallor is True:
        specs.append(
            {
                "rule_id": "iitt_severe_pallor",
                "rule_version": "iitt-2023-reference-card-v1",
                "severity": "medium",
                "trigger_evidence": {"severe_pallor": True},
                "source_observation": {"severe_pallor": True},
            }
        )

    if obs.temperature_c is not None and (obs.temperature_c < 36 or obs.temperature_c > 39):
        specs.append(
            {
                "rule_id": "iitt_high_risk_temperature",
                "rule_version": "iitt-2023-reference-card-v1",
                "severity": "medium",
                "trigger_evidence": {
                    "temperature_c": obs.temperature_c,
                    "threshold": "< 36 C or > 39 C",
                },
                "source_observation": {"temperature_c": obs.temperature_c},
            }
        )

    if obs.respiratory_rate is not None:
        thresholds = {
            "under_5": (25, 50),
            "adult": (10, 30),
            "over_65": (10, 30),
        }
        low, high = thresholds.get(visit.age_band, (10, 30))
        if obs.respiratory_rate < low or obs.respiratory_rate > high:
            specs.append(
                {
                    "rule_id": "iitt_high_risk_respiratory_rate",
                    "rule_version": "iitt-2023-reference-card-v1",
                    "severity": "high",
                    "trigger_evidence": {
                        "respiratory_rate": obs.respiratory_rate,
                        "age_band": visit.age_band,
                        "threshold": f"< {low} or > {high}",
                    },
                    "source_observation": {
                        "respiratory_rate": obs.respiratory_rate,
                        "age_band": visit.age_band,
                    },
                }
            )

    return specs


def create_clinical_alerts(db: Session, obs: PatientObservationSet, visit: Visit, commit: bool = True) -> list[ClinicalReviewAlert]:
    specs = evaluate_iitt_warning_signs(obs, visit)
    alerts: list[ClinicalReviewAlert] = []
    for spec in specs:
        alert = ClinicalReviewAlert(
            visit_id=visit.id,
            observation_set_id=obs.id,
            rule_id=str(spec["rule_id"]),
            rule_version=str(spec["rule_version"]),
            severity=str(spec["severity"]),
            trigger_evidence=dict(spec["trigger_evidence"]),
            source_observation=dict(spec["source_observation"]),
            status="pending",
        )
        db.add(alert)
        alerts.append(alert)
    if alerts and commit:
        db.commit()
        for alert in alerts:
            db.refresh(alert)
    elif alerts:
        db.flush()
        for alert in alerts:
            db.refresh(alert)
    return alerts
