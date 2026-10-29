import uuid
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.mcp.appointment_tools import reserve_appointment_slot
from app.models.domain import AuditEvent, AppointmentRequest, ClinicianDecision, RoleEnum, User


class ApprovalError(Exception):
    pass


def issue_approval_token(
    request_id: uuid.UUID,
    clinician_id: uuid.UUID,
    decision: str,
    reason: str,
) -> str:
    return jwt.encode(
        {
            "purpose": "appointment_commit",
            "jti": str(uuid.uuid4()),
            "request_id": str(request_id),
            "clinician_id": str(clinician_id),
            "decision": decision,
            "reason": reason,
            "exp": datetime.utcnow() + timedelta(minutes=2),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def review_and_commit(db: Session, approval_token: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(
            approval_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        raise ApprovalError("Invalid or expired clinician approval token") from exc

    if claims.get("purpose") != "appointment_commit":
        raise ApprovalError("Token is not authorized for appointment commits")

    try:
        request_id = uuid.UUID(claims["request_id"])
        clinician_id = uuid.UUID(claims["clinician_id"])
        approval_jti = str(uuid.UUID(claims["jti"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise ApprovalError("Malformed clinician approval token") from exc

    clinician = db.get(User, clinician_id)
    if clinician is None or not clinician.is_active or clinician.role not in {
        RoleEnum.SHIFT_LEAD,
        RoleEnum.ADMIN,
    }:
        raise ApprovalError("Approval token does not identify an active clinician")

    request = (
        db.query(AppointmentRequest)
        .filter(AppointmentRequest.id == request_id)
        .with_for_update()
        .first()
    )
    if request is None:
        raise ApprovalError("Appointment request not found")
    if request.status != "PENDING_REVIEW":
        raise ApprovalError("Appointment request has already been decided")

    decision_value = claims.get("decision")
    if decision_value not in {"APPROVE", "REJECT"}:
        raise ApprovalError("Unsupported clinician decision")

    booked_slot_id = None
    if decision_value == "APPROVE":
        if request.proposed_slot_id is None:
            raise ApprovalError("No slot was proposed for this appointment request")
        slot = reserve_appointment_slot(
            db,
            request.proposed_slot_id,
            specialty=request.requested_specialty,
        )
        if slot is None:
            raise ApprovalError("The proposed slot is no longer available")
        request.booked_slot_id = slot.id
        request.status = "BOOKED"
        booked_slot_id = str(slot.id)
    else:
        request.status = "REJECTED"

    decision = ClinicianDecision(
        request_id=request.id,
        clinician_id=clinician.id,
        decision=decision_value,
        reason=claims.get("reason", ""),
        approval_jti=approval_jti,
    )
    db.add(decision)
    db.add(
        AuditEvent(
            actor_id=clinician.id,
            action="CLINICIAN_DECISION",
            entity_type="AppointmentRequest",
            entity_id=str(request.id),
            payload={
                "decision": decision_value,
                "reason": decision.reason,
                "proposed_slot_id": str(request.proposed_slot_id) if request.proposed_slot_id else None,
                "booked_slot_id": booked_slot_id,
                "approval_jti": approval_jti,
            },
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApprovalError("Appointment request has already been committed") from exc
    except Exception:
        db.rollback()
        raise

    return {
        "request_id": str(request.id),
        "decision": decision_value,
        "status": request.status,
        "booked_slot_id": booked_slot_id,
        "clinician_id": str(clinician.id),
    }
