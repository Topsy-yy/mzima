import uuid
from typing import Any
from sqlalchemy.orm import Session

from backend.models.domain import AppointmentRequest
from backend.services.audit.service import log_audit_event


class AppointmentAgentWorkflow:
    """Handles agent appointment proposal workflows with human-in-the-loop enforcement."""

    @staticmethod
    def generate_booking_proposal(
        db: Session,
        patient_identifier: str,
        requested_specialty: str,
        suggested_slot: str,
    ) -> dict[str, Any]:
        """Creates a pending appointment request and marks it strictly as 'PROPOSED_BY_AGENT'.

        The booking CANNOT transition to APPROVED without a human clinician decision.
        """
        app_request = AppointmentRequest(
            patient_identifier=patient_identifier,
            requested_specialty=requested_specialty,
            status="PROPOSED_BY_AGENT",
        )
        db.add(app_request)
        db.commit()
        db.refresh(app_request)

        # Audit that an agent generated this proposal
        log_audit_event(
            db,
            actor_id=None,
            action="AGENT_PROPOSED_BOOKING",
            entity_type="AppointmentRequest",
            entity_id=str(app_request.id),
            payload={
                "patient_identifier": patient_identifier,
                "specialty": requested_specialty,
                "suggested_slot": suggested_slot,
            },
        )

        return {
            "request_id": str(app_request.id),
            "status": app_request.status,
            "message": "Proposal created successfully. Pending clinician decision.",
            "requires_human_approval": True,
        }

    @staticmethod
    def verify_agent_cannot_auto_approve(
        db: Session, request_id: uuid.UUID
    ) -> bool:
        """Safety invariant check confirming the request requires human sign-off."""
        req = (
            db.query(AppointmentRequest)
            .filter(AppointmentRequest.id == request_id)
            .first()
        )
        if not req:
            return False
        # Safety rule: status must NOT be APPROVED directly by agent
        return req.status != "APPROVED"