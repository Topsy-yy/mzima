import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import RoleChecker, get_current_user, get_db
from app.mcp.appointment_tools import get_appointment_slots, reserve_appointment_slot, score_and_propose_route
from app.models.domain import (
    AppointmentRequest,
    ClinicianDecision,
    RoleEnum,
    User,
)
from app.schemas.domain import (
    AppointmentRequestCreate,
    AppointmentRequestResponse,
    AppointmentSlotResponse,
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
    proposal = score_and_propose_route(db, request_in.requested_specialty)
    app_request = AppointmentRequest(
        patient_identifier=request_in.patient_identifier,
        requested_specialty=request_in.requested_specialty,
        status="PENDING_REVIEW",
        proposed_slot_id=uuid.UUID(proposal["slot_id"]) if proposal["slot_id"] else None,
        agent_proposal=proposal,
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
        payload={"specialty": request_in.requested_specialty, "proposal": proposal},
    )

    return app_request


@router.get("/slots", response_model=list[AppointmentSlotResponse])
def list_available_slots(specialty: str, db: Session = Depends(get_db)):
    return get_appointment_slots(db, specialty)


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
        .with_for_update()
        .first()
    )
    if not app_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment request not found",
        )

    if app_request.status != "PENDING_REVIEW":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Appointment request has already been decided",
        )

    if decision_in.decision == "APPROVE":
        if app_request.proposed_slot_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No available slot was proposed; this request cannot be approved as a booking",
            )
        booked_slot = reserve_appointment_slot(db, app_request.proposed_slot_id)
        if booked_slot is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The proposed slot is no longer available",
            )
        app_request.booked_slot_id = booked_slot.id
        app_request.status = "BOOKED"
    else:
        app_request.status = "REJECTED"

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
        payload={
            "decision": decision_in.decision,
            "reason": decision_in.reason,
            "proposed_slot_id": str(app_request.proposed_slot_id) if app_request.proposed_slot_id else None,
            "booked_slot_id": str(app_request.booked_slot_id) if app_request.booked_slot_id else None,
        },
    )

    return decision


@router.get(
    "/appointments/{request_id}",
    response_model=AppointmentRequestResponse,
    dependencies=[
        Depends(
            RoleChecker(
                [RoleEnum.CLERK, RoleEnum.NURSE, RoleEnum.SHIFT_LEAD, RoleEnum.ADMIN]
            )
        )
    ],
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