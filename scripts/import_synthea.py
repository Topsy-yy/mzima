#!/usr/bin/env python3
"""Import Synthea synthetic outpatient data into Mzima flow tables."""

from __future__ import annotations

import csv
import os
import random
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.session import SessionLocal
from app.models.domain import Visit, VisitStatusEnum
from app.models.flow import PatientObservationSet, ClinicalReviewAlert
from app.services.flow.clinical_alerts import evaluate_iitt_warning_signs

DATA_DIR = os.path.join(PROJECT_ROOT, "app", "data", "csv")
ORG_ID = "e002090d-4e92-300e-b41e-7d1f21dee4c6"
MAX_ENCOUNTERS = 1000
TARGET_CLASSES = {"ambulatory", "outpatient", "urgentcare", "emergency"}
ENCOUNTER_WINDOW_DAYS = 7


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value.replace("Z", "+00:00"), "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)


def parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def reset_flow_data(db) -> None:
    db.query(ClinicalReviewAlert).delete(synchronize_session=False)
    db.query(PatientObservationSet).delete(synchronize_session=False)
    db.query(Visit).delete(synchronize_session=False)
    db.commit()


def load_patients() -> dict[str, dict]:
    with open(os.path.join(DATA_DIR, "patients.csv"), newline="") as f:
        return {row["Id"]: row for row in csv.DictReader(f)}


def load_org_encounters() -> list[tuple[int, datetime, dict, datetime]]:
    rows = []
    with open(os.path.join(DATA_DIR, "encounters.csv"), newline="") as f:
        for row in csv.DictReader(f):
            if row["ORGANIZATION"] != ORG_ID or row["ENCOUNTERCLASS"] not in TARGET_CLASSES:
                continue
            try:
                start = parse_dt(row["START"])
                stop = parse_dt(row["STOP"]) if row["STOP"] else start
            except ValueError:
                continue
            rows.append((start, row, stop))
    rows.sort(key=lambda item: item[0])
    if len(rows) > MAX_ENCOUNTERS:
        rows = rows[-MAX_ENCOUNTERS:]
    return [(i, start, row, stop) for i, (start, row, stop) in enumerate(rows)]


def load_observations(selected_encounter_ids: set[str]) -> dict[str, dict[str, float]]:
    by_encounter: dict[str, dict[str, float]] = {}
    wanted = {"Body Temperature", "Heart rate", "Respiratory rate", "Systolic Blood Pressure", "Diastolic Blood Pressure"}
    with open(os.path.join(DATA_DIR, "observations.csv"), newline="") as f:
        for row in csv.DictReader(f):
            enc_id = row["ENCOUNTER"]
            if enc_id not in selected_encounter_ids or row["DESCRIPTION"] not in wanted:
                continue
            try:
                value = float(row["VALUE"])
            except (TypeError, ValueError):
                continue
            obs = by_encounter.setdefault(enc_id, {})
            desc = row["DESCRIPTION"]
            if desc == "Body Temperature":
                obs["temperature_c"] = value
            elif desc == "Heart rate":
                obs["pulse_bpm"] = int(round(value))
            elif desc == "Respiratory rate":
                obs["respiratory_rate"] = int(round(value))
            elif desc == "Systolic Blood Pressure":
                obs["systolic_bp"] = int(round(value))
            elif desc == "Diastolic Blood Pressure":
                obs["diastolic_bp"] = int(round(value))
    return by_encounter


def age_band(patient: dict, encounter_start: datetime) -> str:
    birthdate = parse_date(patient.get("BIRTHDATE", ""))
    if not birthdate:
        return "adult"
    age = (encounter_start.date() - birthdate.date()).days / 365.25
    if age < 5:
        return "under_5"
    if age >= 65:
        return "over_65"
    return "adult"


def visit_type_for(row: dict) -> str:
    desc = (row.get("DESCRIPTION") or "").lower()
    if "follow-up" in desc or "follow up" in desc or "check" in desc:
        return "review"
    if "refill" in desc:
        return "refill"
    return "new"


def reported_symptom_for(row: dict) -> str | None:
    reason = row.get("REASONDESCRIPTION")
    if reason:
        return reason
    desc = row.get("DESCRIPTION")
    if desc and "symptom" in desc.lower():
        return desc
    return None


def main() -> None:
    patients = load_patients()
    selected = load_org_encounters()
    n = len(selected)
    if n == 0:
        raise SystemExit("No encounters selected")
    selected_ids = {row["Id"] for _, _, row, _ in selected}
    observations = load_observations(selected_ids)

    rng = random.Random(2026)
    db = SessionLocal()
    try:
        reset_flow_data(db)
        now = datetime.utcnow()
        window_start = now - timedelta(days=ENCOUNTER_WINDOW_DAYS)

        visit_mappings = []
        obs_mappings = []
        alert_mappings = []
        fast_visit_ids = set()

        for i, original_start, row, original_stop in selected:
            position = i / max(n - 1, 1)
            arrival = window_start + timedelta(seconds=int(position * ENCOUNTER_WINDOW_DAYS * 24 * 3600))
            active_case = i >= n - 60
            if active_case:
                if rng.random() < 0.5:
                    visit_status = VisitStatusEnum.IN_QUEUE.value
                    triage_start_value = None
                    triage_end_value = None
                    first_assessment_start_value = None
                    first_assessment_end_value = None
                    current_stage_value = "arrival"
                else:
                    visit_status = VisitStatusEnum.CALLED.value
                    triage_start_value = arrival + timedelta(minutes=rng.randint(2, 15))
                    triage_end_value = None
                    first_assessment_start_value = None
                    first_assessment_end_value = None
                    current_stage_value = "triage"
            else:
                triage_start_value = arrival + timedelta(minutes=rng.randint(5, 35))
                triage_end_value = triage_start_value + timedelta(minutes=rng.randint(5, 20))
                first_assessment_start_value = triage_end_value + timedelta(minutes=rng.randint(2, 15))
                first_assessment_end_value = first_assessment_start_value + timedelta(minutes=rng.randint(5, 20))
                visit_status = VisitStatusEnum.TRIAGED.value
                current_stage_value = "triaged"

            patient = patients.get(row["PATIENT"], {})
            vitals = observations.get(row["Id"], {})
            reported_symptoms = reported_symptom_for(row) or row.get("DESCRIPTION")
            visit_id = uuid4()
            ab = age_band(patient, original_start)

            visit_obj = SimpleNamespace(age_band=ab, id=visit_id)
            obs_id = uuid4()
            obs_data = {
                "id": obs_id,
                "visit_id": visit_id,
                "temperature_c": vitals.get("temperature_c"),
                "pulse_bpm": vitals.get("pulse_bpm"),
                "respiratory_rate": vitals.get("respiratory_rate"),
                "oxygen_saturation": None,
                "capillary_refill_seconds": None,
                "systolic_bp": vitals.get("systolic_bp"),
                "diastolic_bp": vitals.get("diastolic_bp"),
                "avpu": None,
                "severe_pallor": None,
                "reported_symptoms": reported_symptoms,
                "symptom_summary": {
                    "source": "synthea",
                    "encounter_id": row["Id"],
                    "patient_id": row["PATIENT"],
                    "encounter_class": row["ENCOUNTERCLASS"],
                    "reason_code": row.get("REASONCODE"),
                    "original_start": original_start.isoformat(),
                },
                "data_source": "synthea",
                "generator_name": "synthea",
                "generator_version": "synthetic-healthcare-dataset",
                "collected_at": arrival,
                "created_at": datetime.utcnow(),
                "red_flag_rules_triggered": [],
            }
            alerts = evaluate_iitt_warning_signs(obs_data_to_obj(obs_data), visit_obj)
            is_fast = bool(alerts)

            visit_mappings.append(
                {
                    "id": visit_id,
                    "token_number": f"T-{i + 1:04d}",
                    "arrival_time": arrival,
                    "age_band": ab,
                    "visit_type": visit_type_for(row),
                    "service_point": "cambridge_health_alliance_outpatient",
                    "current_stage": current_stage_value,
                    "status": visit_status,
                    "triage_start_time": triage_start_value,
                    "triage_end_time": triage_end_value,
                    "first_assessment_start_time": first_assessment_start_value,
                    "first_assessment_end_time": first_assessment_end_value,
                    "is_fast_track": is_fast,
                    "red_flags": {"synthea_iitt_alert": True} if is_fast else {},
                    "triage_category": None,
                    "destination": "Consultation",
                }
            )
            obs_mappings.append(obs_data)
            for spec in alerts:
                alert_mappings.append(
                    {
                        "id": uuid4(),
                        "visit_id": visit_id,
                        "observation_set_id": obs_id,
                        "rule_id": str(spec["rule_id"]),
                        "rule_version": str(spec["rule_version"]),
                        "severity": str(spec["severity"]),
                        "trigger_evidence": dict(spec["trigger_evidence"]),
                        "source_observation": dict(spec["source_observation"]),
                        "status": "pending",
                        "created_at": arrival,
                    }
                )

        db.bulk_insert_mappings(Visit, visit_mappings)
        db.bulk_insert_mappings(PatientObservationSet, obs_mappings)
        if alert_mappings:
            db.bulk_insert_mappings(ClinicalReviewAlert, alert_mappings)
        db.commit()

        print(
            "Imported Synthea data:",
            {
                "organization": ORG_ID,
                "encounters_imported": n,
                "observations_imported": len(obs_mappings),
                "clinical_alerts_imported": len(alert_mappings),
                "window_days": ENCOUNTER_WINDOW_DAYS,
            },
            flush=True,
        )
    finally:
        db.close()


def obs_data_to_obj(obs_data):
    class _Obs:
        pass

    obj = _Obs()
    for key, value in obs_data.items():
        setattr(obj, key, value)
    obj.id = obs_data["id"]
    return obj


if __name__ == "__main__":
    main()
