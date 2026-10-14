"""Flow metrics, bottleneck detection, and operational recommendations.

All calculations in this module are deterministic. They do not diagnose,
assign clinical priority, or change queue positions automatically.
"""

from __future__ import annotations

import datetime
import math
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain import Visit, VisitStatusEnum
from app.models.flow import (
    AssessmentStation,
    BottleneckAlert,
    CapacitySnapshot,
    FlowMetricSnapshot,
    OperationalRecommendation,
    OperationalThresholdSet,
    StaffingShift,
)


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def visits_for_window(db: Session, hours: int = 1, service_point: str | None = None):
    cutoff = utcnow() - datetime.timedelta(hours=hours)
    q = db.query(Visit).filter(Visit.arrival_time >= cutoff)
    if service_point:
        q = q.filter(Visit.service_point == service_point)
    return q.all()


def stations_for_point(db: Session, service_point: str | None = None):
    q = db.query(AssessmentStation).filter(AssessmentStation.active.is_(True))
    if service_point:
        q = q.filter(AssessmentStation.service_point == service_point)
    return q.all()


def available_staff_count(db: Session, service_point: str | None = None, now: datetime.datetime | None = None):
    now = now or utcnow()
    q = db.query(StaffingShift).filter(StaffingShift.shift_start <= now, StaffingShift.shift_end >= now)
    if service_point:
        q = q.filter((StaffingShift.service_point == service_point) | (StaffingShift.service_point.is_(None)))
    total = 0
    for shift in q.all():
        total += shift.available_count or 0
    return total


def effective_capacity_per_hour(db: Session, service_point: str | None = None):
    station_capacity = 0
    functional_staffed = 0
    for station in stations_for_point(db, service_point):
        if station.functional and station.staffed:
            station_capacity += station.capacity_per_hour or 0
            functional_staffed += 1
    staff_count = available_staff_count(db, service_point)
    # One staff member is assumed to support one station; excess staff does not increase station throughput.
    if functional_staffed and staff_count < functional_staffed:
        staff_limited_capacity = staff_count * (station_capacity // max(functional_staffed, 1))
        return min(station_capacity, staff_limited_capacity), functional_staffed, staff_count
    return station_capacity, functional_staffed, staff_count


def queue_visits(db: Session, service_point: str | None = None):
    q = db.query(Visit).filter(Visit.status.in_([VisitStatusEnum.IN_QUEUE, VisitStatusEnum.CALLED]))
    if service_point:
        q = q.filter(Visit.service_point == service_point)
    return q.all()


def minutes_between(start: datetime.datetime | None, end: datetime.datetime | None):
    if not start or not end:
        return None
    return int((end - start).total_seconds() / 60)


def wait_metrics(db: Session, service_point: str | None = None):
    now = utcnow()
    visits = queue_visits(db, service_point)
    arrival_to_triage = []
    triage_to_assessment = []
    for visit in visits:
        if visit.triage_start_time:
            arrival_to_triage.append(max(0, int((visit.triage_start_time - visit.arrival_time).total_seconds() / 60)))
        else:
            arrival_to_triage.append(max(0, int((now - visit.arrival_time).total_seconds() / 60)))
        if visit.first_assessment_start_time and visit.triage_end_time:
            triage_to_assessment.append(max(0, int((visit.first_assessment_start_time - visit.triage_end_time).total_seconds() / 60)))
        elif visit.triage_end_time:
            triage_to_assessment.append(max(0, int((now - visit.triage_end_time).total_seconds() / 60)))
    def avg(values):
        return round(sum(values) / len(values), 2) if values else 0.0
    return {
        "queue_length": len(visits),
        "average_wait_for_triage_minutes": avg(arrival_to_triage),
        "average_wait_for_assessment_minutes": avg(triage_to_assessment),
        "max_wait_for_triage_minutes": max(arrival_to_triage) if arrival_to_triage else 0,
        "max_wait_for_assessment_minutes": max(triage_to_assessment) if triage_to_assessment else 0,
    }


def flow_summary(db: Session, service_point: str | None = None) -> dict[str, Any]:
    now = utcnow()
    last_hour_cutoff = now - datetime.timedelta(hours=1)
    arrivals_last_hour = db.query(Visit).filter(Visit.arrival_time >= last_hour_cutoff)
    if service_point:
        arrivals_last_hour = arrivals_last_hour.filter(Visit.service_point == service_point)
    arrivals_last_hour = arrivals_last_hour.count()

    completed_last_hour = db.query(Visit).filter(Visit.triage_end_time >= last_hour_cutoff)
    if service_point:
        completed_last_hour = completed_last_hour.filter(Visit.service_point == service_point)
    completed_last_hour = completed_last_hour.count()

    capacity_per_hour, functional, staff_count = effective_capacity_per_hour(db, service_point)
    utilisation = round(arrivals_last_hour / capacity_per_hour, 3) if capacity_per_hour else 0.0
    wm = wait_metrics(db, service_point)
    summary = {
        "service_point": service_point or "all",
        "snapshot_time": now.isoformat(),
        "arrivals_last_hour": arrivals_last_hour,
        "completed_last_hour": completed_last_hour,
        "queue_length": wm["queue_length"],
        "average_wait_for_triage_minutes": wm["average_wait_for_triage_minutes"],
        "average_wait_for_assessment_minutes": wm["average_wait_for_assessment_minutes"],
        "max_wait_for_triage_minutes": wm["max_wait_for_triage_minutes"],
        "max_wait_for_assessment_minutes": wm["max_wait_for_assessment_minutes"],
        "stations_functional": functional,
        "available_staff": staff_count,
        "capacity_per_hour": capacity_per_hour,
        "utilisation": utilisation,
        "capacity_gap": round(arrivals_last_hour - capacity_per_hour, 3),
    }
    return summary


def get_or_create_threshold_set(db: Session, service_point: str | None = None):
    ts = db.query(OperationalThresholdSet).filter(OperationalThresholdSet.service_point == service_point).first()
    if ts:
        return ts
    global_ts = db.query(OperationalThresholdSet).filter(OperationalThresholdSet.service_point.is_(None)).first()
    if global_ts:
        return global_ts
    ts = OperationalThresholdSet(name="default-thresholds", service_point=service_point, approved=False)
    db.add(ts)
    db.commit()
    db.refresh(ts)
    return ts


def detect_bottlenecks(db: Session, service_points: list[str | None] | None = None):
    points = service_points if service_points is not None else [None]
    threshold_cache = {}
    alerts = []
    now = utcnow()
    dedupe_cutoff = now - datetime.timedelta(minutes=30)
    for point in points:
        summary = flow_summary(db, point)
        threshold = get_or_create_threshold_set(db, point)
        threshold_cache[point] = threshold

        def add_alert(metric_name, metric_value, threshold_value, severity, code):
            existing = db.query(BottleneckAlert).filter(
                BottleneckAlert.service_point == (point or "all"),
                BottleneckAlert.metric_name == metric_name,
                BottleneckAlert.created_at >= dedupe_cutoff,
                BottleneckAlert.status == "pending",
            ).first()
            if existing:
                return existing
            alert = BottleneckAlert(
                alert_code=code,
                service_point=point or "all",
                severity=severity,
                metric_name=metric_name,
                metric_value=float(metric_value),
                threshold_value=float(threshold_value),
                evidence=summary,
                threshold_set_version=threshold.version,
                status="pending",
            )
            db.add(alert)
            alerts.append(alert)
            return alert

        if summary["average_wait_for_triage_minutes"] > threshold.max_wait_for_triage_minutes:
            add_alert(
                "average_wait_for_triage_minutes",
                summary["average_wait_for_triage_minutes"],
                threshold.max_wait_for_triage_minutes,
                "medium",
                "wait_for_triage_sla_breach",
            )
        if summary["average_wait_for_assessment_minutes"] > threshold.max_wait_for_assessment_minutes:
            add_alert(
                "average_wait_for_assessment_minutes",
                summary["average_wait_for_assessment_minutes"],
                threshold.max_wait_for_assessment_minutes,
                "medium",
                "wait_for_assessment_sla_breach",
            )
        if threshold.utilisation_critical_threshold and summary["utilisation"] >= threshold.utilisation_critical_threshold:
            add_alert(
                "utilisation",
                summary["utilisation"],
                threshold.utilisation_critical_threshold,
                "critical",
                "capacity_utilisation_critical",
            )
        elif threshold.utilisation_warning_threshold and summary["utilisation"] >= threshold.utilisation_warning_threshold:
            add_alert(
                "utilisation",
                summary["utilisation"],
                threshold.utilisation_warning_threshold,
                "medium",
                "capacity_utilisation_warning",
            )
        if summary["queue_length"] >= threshold.queue_growth_warning_threshold and summary["capacity_gap"] > 0:
            add_alert(
                "capacity_gap",
                summary["capacity_gap"],
                threshold.queue_growth_warning_threshold,
                "medium",
                "arrival_volume_exceeds_capacity",
            )

    if alerts:
        db.commit()
        for alert in alerts:
            db.refresh(alert)
    return alerts


def generate_operational_recommendations(db: Session, service_points: list[str | None] | None = None):
    points = service_points if service_points is not None else [None]
    recommendations = []
    now = utcnow()
    dedupe_cutoff = now - datetime.timedelta(minutes=60)
    for point in points:
        summary = flow_summary(db, point)
        if summary["utilisation"] >= 1.0 or summary["capacity_gap"] > 0:
            existing = db.query(OperationalRecommendation).filter(
                OperationalRecommendation.service_point == (point or "all"),
                OperationalRecommendation.recommendation_type == "review_staffing_or_station_capacity",
                OperationalRecommendation.created_at >= dedupe_cutoff,
                OperationalRecommendation.status == "pending",
            ).first()
            if not existing:
                projected_reduction = round(summary["average_wait_for_triage_minutes"] * 0.25, 2) if summary["average_wait_for_triage_minutes"] else None
                rec = OperationalRecommendation(
                    recommendation_type="review_staffing_or_station_capacity",
                    service_point=point or "all",
                    suggested_action=(
                        "Shift supervisor should review whether an additional staffed assessment station "
                        "or safe staff reallocation can be added for this service point."
                    ),
                    rationale=(
                        "Arrivals in the last hour exceeded or met the currently effective station capacity, "
                        "creating a queue and wait-time risk."
                    ),
                    projected_wait_reduction_minutes=projected_reduction,
                    projected_queue_reduction=max(1, int(summary["capacity_gap"])) if summary["capacity_gap"] > 0 else None,
                    evidence=summary,
                    status="pending",
                )
                db.add(rec)
                recommendations.append(rec)
        elif summary["queue_length"] >= 5 and summary["average_wait_for_triage_minutes"] > 0:
            existing = db.query(OperationalRecommendation).filter(
                OperationalRecommendation.service_point == (point or "all"),
                OperationalRecommendation.recommendation_type == "review_queue_flow",
                OperationalRecommendation.created_at >= dedupe_cutoff,
                OperationalRecommendation.status == "pending",
            ).first()
            if not existing:
                rec = OperationalRecommendation(
                    recommendation_type="review_queue_flow",
                    service_point=point or "all",
                    suggested_action="Shift supervisor should review queue flow and identify where patients are waiting longest.",
                    rationale="Queue length and wait times indicate emerging pressure even before hard capacity breach.",
                    evidence=summary,
                    status="pending",
                )
                db.add(rec)
                recommendations.append(rec)
    if recommendations:
        db.commit()
        for rec in recommendations:
            db.refresh(rec)
    return recommendations


def record_capacity_snapshot(db: Session, service_point: str | None = None):
    summary = flow_summary(db, service_point)
    station_capacity, functional, staff_count = effective_capacity_per_hour(db, service_point)
    snapshot = CapacitySnapshot(
        service_point=service_point,
        staff_available={"available_staff": staff_count},
        stations_functional=functional,
        stations_staffed=functional,
        arrivals_last_hour=summary["arrivals_last_hour"],
        completed_last_hour=summary["completed_last_hour"],
        queue_length=summary["queue_length"],
        utilisation=summary["utilisation"],
        capacity_gap=summary["capacity_gap"],
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def record_flow_metric_snapshot(db: Session, service_point: str | None = None):
    summary = flow_summary(db, service_point)
    snapshot = FlowMetricSnapshot(
        service_point=service_point,
        queue_length=summary["queue_length"],
        arrivals=summary["arrivals_last_hour"],
        completed=summary["completed_last_hour"],
        avg_wait_for_triage_minutes=summary["average_wait_for_triage_minutes"],
        avg_wait_for_assessment_minutes=summary["average_wait_for_assessment_minutes"],
        sla_breach_count=0,
        utilisation=summary["utilisation"],
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
