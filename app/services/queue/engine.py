from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.domain import Visit, VisitStatusEnum
from backend.schemas.domain import QueueItemResponse


def get_weighted_queue(db: Session) -> list[QueueItemResponse]:
    """Ranks active queue tokens according to Mzima specs:

    1. Red-flag fast-tracks go to the top.
    2. Wait cap (>120 min) promotes token.
    3. Score = minutes_waited * age_weight (1.5 for under_5 / over_65, 1.0 otherwise).
    """
    now = datetime.utcnow()
    visits = (
        db.query(Visit)
        .filter(Visit.status == VisitStatusEnum.IN_QUEUE)
        .order_by(Visit.arrival_time.asc())
        .all()
    )

    queue_items = []
    for visit in visits:
        minutes_waited = max(0, int((now - visit.arrival_time).total_seconds() / 60))

        # Weighting rules: 1.5 for under_5 or over_65
        weight = 1.5 if visit.age_band in ["under_5", "over_65"] else 1.0
        calculated_score = minutes_waited * weight
        is_wait_capped = minutes_waited >= 120

        queue_items.append(
            QueueItemResponse(
                visit_id=visit.id,
                token_number=visit.token_number,
                arrival_time=visit.arrival_time,
                minutes_waiting=minutes_waited,
                is_fast_track=visit.is_fast_track,
                is_wait_capped=is_wait_capped,
                calculated_score=calculated_score,
                red_flags=visit.red_flags or {},
            )
        )

    # Sorting order: fast-track first, then wait-capped, then highest calculated score
    queue_items.sort(
        key=lambda x: (
            not x.is_fast_track,
            not x.is_wait_capped,
            -x.calculated_score,
        )
    )

    return queue_items