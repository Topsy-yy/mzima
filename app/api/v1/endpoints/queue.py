import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import RoleChecker, get_current_user, get_db
from app.models.domain import QueueEvent, RoleEnum, User, Visit, VisitStatusEnum
from app.schemas.domain import (
    CallTokenRequest,
    QueueItemResponse,
    TriageUpdate,
    VisitCreate,
    VisitResponse,
)
from app.services.audit.service import log_audit_event
from app.services.queue.engine import get_weighted_queue

router = APIRouter()


@router.post(
    "/visits",
    response_model=VisitResponse,
    dependencies=[Depends(RoleChecker([RoleEnum.CLERK, RoleEnum.ADMIN]))],
)
def check_in_patient(
    visit_in: VisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Auto-generate token number
    today_count = db.query(Visit).count() + 1
    token_num = f"T-{today_count:03d}"

    is_fast_track = any(visit_in.red_flags.values())

    visit = Visit(
        token_number=token_num,
        age_band=visit_in.age_band,
        visit_type=visit_in.visit_type,
        is_fast_track=is_fast_track,
        red_flags=visit_in.red_flags,
        status=VisitStatusEnum.IN_QUEUE,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    log_audit_event(
        db,
        actor_id=current_user.id,
        action="CHECK_IN",
        entity_type="Visit",
        entity_id=str(visit.id),
        payload={"token_number": token_num, "is_fast_track": is_fast_track},
    )

    return visit


@router.get(
    "/queue",
    response_model=list[QueueItemResponse],
    dependencies=[
        Depends(
            RoleChecker(
                [RoleEnum.CLERK, RoleEnum.NURSE, RoleEnum.SHIFT_LEAD, RoleEnum.ADMIN]
            )
        )
    ],
)
def get_review_queue(db: Session = Depends(get_db)):
    return get_weighted_queue(db)


@router.post(
    "/queue/{visit_id}/call",
    response_model=VisitResponse,
    dependencies=[
        Depends(RoleChecker([RoleEnum.NURSE, RoleEnum.SHIFT_LEAD, RoleEnum.ADMIN]))
    ],
)
def call_next_patient(
    visit_id: uuid.UUID,
    call_in: CallTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visit token not found"
        )

    visit.status = VisitStatusEnum.CALLED
    visit.triage_start_time = datetime.utcnow()

    event = QueueEvent(
        visit_id=visit.id,
        actor_id=current_user.id,
        event_type="CALL" if not call_in.override_reason else "OVERRIDE",
        reason_code=call_in.override_reason,
    )
    db.add(event)
    db.commit()
    db.refresh(visit)

    log_audit_event(
        db,
        actor_id=current_user.id,
        action="CALL_PATIENT",
        entity_type="Visit",
        entity_id=str(visit.id),
        payload={"override_reason": call_in.override_reason},
    )

    return visit


@router.post(
    "/visits/{visit_id}/triage",
    response_model=VisitResponse,
    dependencies=[
        Depends(RoleChecker([RoleEnum.NURSE, RoleEnum.SHIFT_LEAD, RoleEnum.ADMIN]))
    ],
)
def complete_triage(
    visit_id: uuid.UUID,
    triage_in: TriageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visit token not found"
        )

    visit.status = VisitStatusEnum.TRIAGED
    visit.triage_end_time = datetime.utcnow()
    visit.triage_category = triage_in.triage_category
    visit.destination = triage_in.destination

    db.commit()
    db.refresh(visit)

    log_audit_event(
        db,
        actor_id=current_user.id,
        action="COMPLETE_TRIAGE",
        entity_type="Visit",
        entity_id=str(visit.id),
        payload={
            "triage_category": triage_in.triage_category,
            "destination": triage_in.destination,
        },
    )

    return visit