from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.domain import AppointmentSlot


def get_appointment_slots(
    db: Session, specialty: str, now: datetime | None = None
) -> list[AppointmentSlot]:
    current_time = now or datetime.utcnow()
    return (
        db.query(AppointmentSlot)
        .filter(
            AppointmentSlot.specialty == specialty,
            AppointmentSlot.starts_at >= current_time,
            AppointmentSlot.booked_count < AppointmentSlot.capacity,
        )
        .order_by(AppointmentSlot.starts_at)
        .all()
    )


def score_and_propose_route(
    db: Session, specialty: str, now: datetime | None = None
) -> dict[str, Any]:
    slots = get_appointment_slots(db, specialty, now)
    if not slots:
        return {
            "tool": "score_and_propose_route",
            "status": "NO_MATCH",
            "specialty": specialty,
            "slot_id": None,
            "evidence": ["No available synthetic slot matches the requested service."],
            "rule_version": "synthetic-slots-v1",
        }

    slot = slots[0]
    return {
        "tool": "score_and_propose_route",
        "status": "PENDING_CLINICIAN_REVIEW",
        "specialty": specialty,
        "slot_id": str(slot.id),
        "starts_at": slot.starts_at.isoformat(),
        "evidence": [
            "Requested service exactly matches the configured slot service.",
            "Slot has remaining capacity at proposal time.",
            "Earliest available matching slot selected; no clinical priority inferred.",
        ],
        "rule_version": "synthetic-slots-v1",
    }


def reserve_appointment_slot(db: Session, slot_id: uuid.UUID) -> AppointmentSlot | None:
    result = db.execute(
        update(AppointmentSlot)
        .where(
            AppointmentSlot.id == slot_id,
            AppointmentSlot.booked_count < AppointmentSlot.capacity,
        )
        .values(booked_count=AppointmentSlot.booked_count + 1)
    )
    if result.rowcount != 1:
        return None
    db.flush()
    db.expire_all()
    return db.get(AppointmentSlot, slot_id)