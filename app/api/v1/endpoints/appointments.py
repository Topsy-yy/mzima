import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import RoleChecker, get_current_user, get_db
from app.models.domain import (
    AppointmentRequest,
    ClinicianDecision,
    RoleEnum,
    User,
)
from app.schemas.domain import (
    AppointmentRequestCreate,
    AppointmentRequestResponse,
    ClinicianDecisionCreate,
    ClinicianDecisionResponse,
)
from app.services.audit.service import log_audit_event

router = APIRouter()


@router.post(
    "/appointment-requests",
    response_model=AppointmentRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_appointment_request(
    request_in: AppointmentRequestCreate, db: Session = Depends(get_db)
):
    app_request = AppointmentRequest(
        patient_identifier=request_in.patient_identifier,
        requested_specialty=request_in.requested_specialty,
        status="PENDING_REVIEW",
    )
    db.add(app_request)
    db.commit()
    db.refresh(app_request)

    log_audit_event(
        db,
        actor_id=None,
        action="SUBMIT_APPOINTMENT_REQUEST",
        entity_type="AppointmentRequest",
        entity_id=str(app_request.id),
        payload={"specialty": request_in.requested_specialty},
    )

    return app_request


@router.get(
    "/clinic/review-queue",
    response_model=list[AppointmentRequestResponse],
    dependencies=[
        Depends(RoleChecker([RoleEnum.SHIFT_LEAD, RoleEnum.ADMIN]))
    ],
)
def get_appointment_review_queue(db: Session = Depends(get_db)):
    return (
        db.query(AppointmentRequest)
        .filter(AppointmentRequest.status == "PENDING_REVIEW")
        .all()
    )


@router.post(
    "/appointment-requests/{request_id}/decision",
    response_model=ClinicianDecisionResponse,
    dependencies=[
        Depends(RoleChecker([RoleEnum.SHIFT_LEAD, RoleEnum.ADMIN]))
    ],
)
def submit_clinician_decision(
    request_id: uuid.UUID,
    decision_in: ClinicianDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_request = (
        db.query(AppointmentRequest)
        .filter(AppointmentRequest.id == request_id)
        .first()
    )
    if not app_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment request not found",
        )

    app_request.status = (
        "APPROVED" if decision_in.decision == "APPROVE" else "REJECTED"
    )

    decision = ClinicianDecision(
        request_id=app_request.id,
        clinician_id=current_user.id,
        decision=decision_in.decision,
        reason=decision_in.reason,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    log_audit_event(
        db,
        actor_id=current_user.id,
        action="CLINICIAN_DECISION",
        entity_type="AppointmentRequest",
        entity_id=str(app_request.id),
        payload={"decision": decision_in.decision, "reason": decision_in.reason},
    )

    return decision


@router.get(
    "/appointments/{request_id}", response_model=AppointmentRequestResponse
)
def get_appointment_details(request_id: uuid.UUID, db: Session = Depends(get_db)):
    app_request = (
        db.query(AppointmentRequest)
        .filter(AppointmentRequest.id == request_id)
        .first()
    )
    if not app_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment request not found",
        )
    return app_request