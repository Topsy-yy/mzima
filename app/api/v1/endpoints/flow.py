"""Flow-optimisation API endpoints for Mzima."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import RoleChecker, get_current_user, get_db
from app.core.config import settings
from app.models.domain import User, Visit
from app.models.flow import (
    AssessmentStation,
    BottleneckAlert,
    ClinicalReviewAlert,
    ClinicalReviewOutcome,
    FlowMetricSnapshot,
    OperationalRecommendation,
    OperationalThresholdSet,
    PatientObservationSet,
    SimulationResult,
    SimulationScenario,
    StaffingShift,
    TriageSourceDocument,
)
from app.schemas.flow import (
    BottleneckScanRequest,
    ClinicalAlertReviewCreate,
    ObservationCreate,
    RecommendationReviewCreate,
    SimulationRequest,
    StationCreate,
    StationStatusUpdate,
    StaffingCreate,
    TextExtractionRequest,
)
from app.services.flow.capacity import (
    detect_bottlenecks,
    effective_capacity_per_hour,
    flow_summary,
    generate_operational_recommendations,
    get_or_create_threshold_set,
    record_capacity_snapshot,
    record_flow_metric_snapshot,
    wait_metrics,
)
from app.services.flow.clinical_alerts import create_clinical_alerts
from app.services.flow.llm_extraction import extract_observation_fields
from app.services.flow.simulation import simulate_capacity_scenario

router = APIRouter(prefix="/flow", tags=["flow optimisation"])


def _role(*roles):
    return Depends(RoleChecker(list(roles)))


@router.get("/summary")
def get_flow_summary(
    service_point: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return flow_summary(db, service_point)


@router.get("/wait-metrics")
def get_wait_metrics(
    service_point: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return wait_metrics(db, service_point)


@router.post("/metric-snapshots")
def create_metric_snapshot(
    service_point: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    snapshot = record_flow_metric_snapshot(db, service_point)
    return {"id": str(snapshot.id), "service_point": snapshot.service_point, "metric_time": snapshot.metric_time.isoformat()}


@router.get("/metric-snapshots")
def list_metric_snapshots(
    service_point: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(FlowMetricSnapshot)
    if service_point:
        q = q.filter(FlowMetricSnapshot.service_point == service_point)
    rows = q.order_by(FlowMetricSnapshot.metric_time.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "service_point": r.service_point,
            "metric_time": r.metric_time.isoformat(),
            "queue_length": r.queue_length,
            "arrivals": r.arrivals,
            "completed": r.completed,
            "avg_wait_for_triage_minutes": r.avg_wait_for_triage_minutes,
            "avg_wait_for_assessment_minutes": r.avg_wait_for_assessment_minutes,
            "utilisation": r.utilisation,
        }
        for r in rows
    ]


@router.get("/stations")
def list_stations(
    service_point: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AssessmentStation).filter(AssessmentStation.active.is_(True))
    if service_point:
        q = q.filter(AssessmentStation.service_point == service_point)
    rows = q.order_by(AssessmentStation.station_code.asc()).all()
    return [
        {
            "id": str(r.id),
            "station_code": r.station_code,
            "name": r.name,
            "service_point": r.service_point,
            "zone_code": r.zone_code,
            "functional": r.functional,
            "staffed": r.staffed,
            "capacity_per_hour": r.capacity_per_hour,
            "required_role": r.required_role,
        }
        for r in rows
    ]


@router.post("/stations", status_code=status.HTTP_201_CREATED)
def create_station(
    payload: StationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "shift_lead"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    station = AssessmentStation(
        station_code=payload.station_code,
        name=payload.name,
        service_point=payload.service_point,
        zone_code=payload.zone_code,
        functional=payload.functional,
        staffed=payload.staffed,
        capacity_per_hour=payload.capacity_per_hour,
        required_role=payload.required_role,
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return {"id": str(station.id), "station_code": station.station_code}


@router.patch("/stations/{station_id}")
def update_station(
    station_id: uuid.UUID,
    payload: StationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "shift_lead"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    station = db.query(AssessmentStation).filter(AssessmentStation.id == station_id).first()
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
    if payload.functional is not None:
        station.functional = payload.functional
    if payload.staffed is not None:
        station.staffed = payload.staffed
    if payload.capacity_per_hour is not None:
        station.capacity_per_hour = payload.capacity_per_hour
    station.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(station)
    return {"id": str(station.id), "functional": station.functional, "staffed": station.staffed, "capacity_per_hour": station.capacity_per_hour}


@router.get("/staffing")
def list_staffing(
    service_point: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(StaffingShift)
    if service_point:
        q = q.filter((StaffingShift.service_point == service_point) | (StaffingShift.service_point.is_(None)))
    rows = q.order_by(StaffingShift.shift_start.asc()).all()
    return [
        {
            "id": str(r.id),
            "shift_start": r.shift_start.isoformat(),
            "shift_end": r.shift_end.isoformat(),
            "role": r.role,
            "service_point": r.service_point,
            "planned_count": r.planned_count,
            "available_count": r.available_count,
            "notes": r.notes,
        }
        for r in rows
    ]


@router.post("/staffing", status_code=status.HTTP_201_CREATED)
def create_staffing(
    payload: StaffingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "shift_lead"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    shift = StaffingShift(**payload.model_dump())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return {"id": str(shift.id)}


@router.post("/capacity/snapshot")
def create_capacity_snapshot(
    service_point: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    snapshot = record_capacity_snapshot(db, service_point)
    _, functional, staff_count = effective_capacity_per_hour(db, service_point)
    capacity_per_hour = snapshot.arrivals_last_hour and "n/a"
    return {
        "id": str(snapshot.id),
        "service_point": snapshot.service_point,
        "snapshot_time": snapshot.snapshot_time.isoformat(),
        "stations_functional": snapshot.stations_functional,
        "available_staff": snapshot.staff_available,
        "utilisation": snapshot.utilisation,
        "capacity_gap": snapshot.capacity_gap,
    }


@router.post("/bottleneck-scan")
def run_bottleneck_scan(
    payload: BottleneckScanRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "shift_lead", "nurse"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    points = payload.service_points if payload else None
    alerts = detect_bottlenecks(db, points)
    return {
        "alerts_created_or_found": len(alerts),
        "alert_ids": [str(a.id) for a in alerts],
    }


@router.get("/bottlenecks")
def list_bottlenecks(
    service_point: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(BottleneckAlert)
    if service_point:
        q = q.filter(BottleneckAlert.service_point == service_point)
    if status_filter:
        q = q.filter(BottleneckAlert.status == status_filter)
    rows = q.order_by(BottleneckAlert.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "alert_code": r.alert_code,
            "service_point": r.service_point,
            "severity": r.severity,
            "metric_name": r.metric_name,
            "metric_value": r.metric_value,
            "threshold_value": r.threshold_value,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "reason": r.reason,
        }
        for r in rows
    ]


@router.post("/bottlenecks/{alert_id}/review")
def review_bottleneck(
    alert_id: uuid.UUID,
    payload: RecommendationReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(BottleneckAlert).filter(BottleneckAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bottleneck alert not found")
    if current_user.role.value not in {"admin", "shift_lead"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    alert.status = payload.decision
    alert.reason = payload.reason
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return {"id": str(alert.id), "status": alert.status}


@router.post("/recommendations/scan")
def run_recommendation_scan(
    payload: BottleneckScanRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "shift_lead", "nurse"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    points = payload.service_points if payload else None
    recommendations = generate_operational_recommendations(db, points)
    return {"recommendations_created_or_found": len(recommendations), "ids": [str(r.id) for r in recommendations]}


@router.get("/recommendations")
def list_recommendations(
    service_point: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(OperationalRecommendation)
    if service_point:
        q = q.filter(OperationalRecommendation.service_point == service_point)
    if status_filter:
        q = q.filter(OperationalRecommendation.status == status_filter)
    rows = q.order_by(OperationalRecommendation.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "recommendation_type": r.recommendation_type,
            "service_point": r.service_point,
            "suggested_action": r.suggested_action,
            "rationale": r.rationale,
            "projected_wait_reduction_minutes": r.projected_wait_reduction_minutes,
            "projected_queue_reduction": r.projected_queue_reduction,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "reason": r.reason,
        }
        for r in rows
    ]


@router.post("/recommendations/{recommendation_id}/review")
def review_recommendation(
    recommendation_id: uuid.UUID,
    payload: RecommendationReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = db.query(OperationalRecommendation).filter(OperationalRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    if current_user.role.value not in {"admin", "shift_lead"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    rec.status = payload.decision
    rec.reason = payload.reason
    rec.reviewed_by = current_user.id
    rec.reviewed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return {"id": str(rec.id), "status": rec.status}


@router.get("/clinical-alerts")
def list_clinical_alerts(
    visit_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "shift_lead", "nurse"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    q = db.query(ClinicalReviewAlert)
    if visit_id:
        q = q.filter(ClinicalReviewAlert.visit_id == visit_id)
    if status_filter:
        q = q.filter(ClinicalReviewAlert.status == status_filter)
    rows = q.order_by(ClinicalReviewAlert.created_at.desc()).limit(limit).all()
    out = []
    for alert in rows:
        obs = db.query(PatientObservationSet).filter(PatientObservationSet.id == alert.observation_set_id).first() if alert.observation_set_id else None
        out.append(
            {
                "id": str(alert.id),
                "visit_id": str(alert.visit_id),
                "rule_id": alert.rule_id,
                "rule_version": alert.rule_version,
                "severity": alert.severity,
                "trigger_evidence": alert.trigger_evidence,
                "source_observation": alert.source_observation,
                "status": alert.status,
                "created_at": alert.created_at.isoformat(),
                "reported_symptoms": obs.reported_symptoms if obs else None,
                "temperature_c": obs.temperature_c if obs else None,
                "pulse_bpm": obs.pulse_bpm if obs else None,
                "oxygen_saturation": obs.oxygen_saturation if obs else None,
                "avpu": obs.avpu if obs else None,
            }
        )
    return out


@router.post("/clinical-alerts/{alert_id}/review")
def review_clinical_alert(
    alert_id: uuid.UUID,
    payload: ClinicalAlertReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "shift_lead", "nurse"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    alert = db.query(ClinicalReviewAlert).filter(ClinicalReviewAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical alert not found")
    resolved_statuses = {"reviewed", "dismissed", "escalated", "acknowledged"}
    if payload.decision not in resolved_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review decision")
    alert.status = payload.decision
    alert.resolved_at = datetime.datetime.utcnow()
    outcome = ClinicalReviewOutcome(
        alert_id=alert.id,
        reviewer_id=current_user.id,
        reviewer_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        decision=payload.decision,
        reason=payload.reason,
    )
    db.add(outcome)
    db.commit()
    db.refresh(alert)
    return {"id": str(alert.id), "status": alert.status}


@router.get("/observations")
def list_observations(
    visit_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(PatientObservationSet)
    if visit_id:
        q = q.filter(PatientObservationSet.visit_id == visit_id)
    rows = q.order_by(PatientObservationSet.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "visit_id": str(r.visit_id),
            "temperature_c": r.temperature_c,
            "pulse_bpm": r.pulse_bpm,
            "respiratory_rate": r.respiratory_rate,
            "oxygen_saturation": r.oxygen_saturation,
            "capillary_refill_seconds": r.capillary_refill_seconds,
            "systolic_bp": r.systolic_bp,
            "diastolic_bp": r.diastolic_bp,
            "avpu": r.avpu,
            "severe_pallor": r.severe_pallor,
            "reported_symptoms": r.reported_symptoms,
            "symptom_summary": r.symptom_summary,
            "data_source": r.data_source,
            "collected_at": r.collected_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/observations", status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in {"admin", "shift_lead", "nurse", "clerk"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    visit = db.query(Visit).filter(Visit.id == payload.visit_id).first()
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    obs = PatientObservationSet(
        visit_id=payload.visit_id,
        temperature_c=payload.temperature_c,
        pulse_bpm=payload.pulse_bpm,
        respiratory_rate=payload.respiratory_rate,
        oxygen_saturation=payload.oxygen_saturation,
        capillary_refill_seconds=payload.capillary_refill_seconds,
        systolic_bp=payload.systolic_bp,
        diastolic_bp=payload.diastolic_bp,
        avpu=payload.avpu,
        severe_pallor=payload.severe_pallor,
        reported_symptoms=payload.reported_symptoms,
        symptom_summary=payload.symptom_summary,
        data_source=payload.data_source,
    )
    db.add(obs)
    db.flush()
    alerts = create_clinical_alerts(db, obs, visit, commit=False)
    visit.service_point = visit.service_point or "main_outpatient"
    db.commit()
    db.refresh(obs)
    return {"id": str(obs.id), "alerts_created": len(alerts), "alert_ids": [str(a.id) for a in alerts]}


@router.post("/observations/extract")
def extract_observation(
    payload: TextExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.AGENTROUTER_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AgentRouter is not configured")
    try:
        extracted = extract_observation_fields(payload.text)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Extraction failed: {exc}")
    if payload.visit_id:
        visit = db.query(Visit).filter(Visit.id == payload.visit_id).first()
        if not visit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return {"extracted_fields": extracted, "requires_human_review": True}


@router.get("/triage-sources")
def list_triage_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.query(TriageSourceDocument).order_by(TriageSourceDocument.title.asc()).all()
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "source_type": r.source_type,
            "publisher": r.publisher,
            "license": r.license,
            "source_url": r.source_url,
            "ingestion_status": r.ingestion_status,
            "extracted_text_characters": len(r.extracted_text or ""),
        }
        for r in rows
    ]


@router.get("/public-health-context")
def list_public_health_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.query(PublicHealthContext if False else None).all() if False else []
    # Public health context is currently documented in source controls; no invented statistics are returned.
    return {
        "status": "not_seeded",
        "message": "No public-health statistics have been entered yet. Add only verified WHO, Ministry of Health, or county sources with date and geography.",
    }


@router.post("/simulations", status_code=status.HTTP_201_CREATED)
def create_simulation(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import statistics
    arrivals = payload.baseline_arrivals_per_hour
    if arrivals is None:
        recent = flow_summary(db, None)
        arrivals = float(recent["arrivals_last_hour"] or 12)
    scenario = SimulationScenario(
        name=payload.name,
        description=payload.description,
        parameters=payload.model_dump(),
        created_by=payload.created_by or current_user.username,
    )
    db.add(scenario)
    db.flush()
    result_data = simulate_capacity_scenario(
        baseline_arrivals_per_hour=arrivals,
        baseline_service_minutes=payload.baseline_service_minutes,
        baseline_stations=payload.baseline_stations,
        scenario_stations=payload.scenario_stations,
        scenario_staff=payload.scenario_staff,
        scenario_service_minutes=payload.scenario_service_minutes,
    )
    result = SimulationResult(
        scenario_id=scenario.id,
        baseline_metrics=result_data["baseline"],
        scenario_metrics=result_data["scenario"],
        assumptions=result_data["assumptions"],
    )
    result_data["id"] = str(scenario.id)
    result_data["result_id"] = str(result.id)
    db.add(result)
    db.commit()
    db.refresh(scenario)
    db.refresh(result)
    return result_data


@router.get("/simulations/{scenario_id}")
def get_simulation(
    scenario_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scenario = db.query(SimulationScenario).filter(SimulationScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found")
    result = db.query(SimulationResult).filter(SimulationResult.scenario_id == scenario_id).order_by(SimulationResult.created_at.desc()).first()
    return {
        "scenario": {
            "id": str(scenario.id),
            "name": scenario.name,
            "description": scenario.description,
            "parameters": scenario.parameters,
            "created_at": scenario.created_at.isoformat(),
        },
        "result": {
            "id": str(result.id) if result else None,
            "baseline_metrics": result.baseline_metrics if result else None,
            "scenario_metrics": result.scenario_metrics if result else None,
            "assumptions": result.assumptions if result else None,
        },
    }
