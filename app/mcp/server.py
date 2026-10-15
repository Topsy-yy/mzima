import json
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.domain import AppointmentRequest
from app.services.queue.engine import get_weighted_queue


class ReadOnlyMzimaMCP:
    """Read-only MCP interface for querying synthetic queue states and forecasts."""

    @staticmethod
    def get_live_queue_summary() -> str:
        """Fetches ranked queue metrics and top active waiting tokens."""
        db: Session = SessionLocal()
        try:
            queue = get_weighted_queue(db)
            summary = {
                "total_in_queue": len(queue),
                "fast_track_count": sum(1 for item in queue if item.is_fast_track),
                "wait_capped_count": sum(1 for item in queue if item.is_wait_capped),
                "top_tokens": [item.model_dump() for item in queue[:5]],
            }
            return json.dumps(summary, default=str)
        finally:
            db.close()

    @staticmethod
    def get_pending_appointment_reviews() -> str:
        """Retrieves all appointment requests currently awaiting clinician decision."""
        db: Session = SessionLocal()
        try:
            requests = (
                db.query(AppointmentRequest)
                .filter(AppointmentRequest.status == "PENDING_REVIEW")
                .all()
            )
            data = [
                {
                    "id": str(req.id),
                    "patient_identifier": req.patient_identifier,
                    "specialty": req.requested_specialty,
                    "created_at": req.created_at.isoformat(),
                }
                for req in requests
            ]
            return json.dumps(data)
        finally:
            db.close()