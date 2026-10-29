import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal
from app.mcp.appointment_tools import get_appointment_slots, score_and_propose_route
from app.models.domain import AppointmentRequest, AuditEvent
from app.services.appointments.workflow import ApprovalError, review_and_commit


def create_mcp_server(
    session_factory: Callable[[], Session] = SessionLocal,
) -> FastMCP:
    server = FastMCP(
        "Mzima Synthetic Appointment Tools",
        instructions=(
            "Synthetic appointment workflow tools. Slot proposals are not clinical advice. "
            "Only review_and_commit with a signed, short-lived clinician token can book."
        ),
    )

    @server.tool()
    def get_appointment_slots_tool(specialty: str) -> dict[str, Any]:
        """List future synthetic appointment slots with remaining capacity for one service."""
        with session_factory() as db:
            slots = get_appointment_slots(db, specialty)
            result = [
                {
                    "id": str(slot.id),
                    "specialty": slot.specialty,
                    "starts_at": slot.starts_at.isoformat(),
                    "remaining": slot.capacity - slot.booked_count,
                }
                for slot in slots
            ]
            db.add(
                AuditEvent(
                    actor_id=None,
                    action="MCP_GET_APPOINTMENT_SLOTS",
                    entity_type="AppointmentSlotQuery",
                    entity_id=specialty,
                    timestamp=datetime.utcnow(),
                    payload={"specialty": specialty, "result_count": len(result)},
                )
            )
            db.commit()
            return {"specialty": specialty, "slots": result}

    @server.tool()
    def score_and_propose_route_tool(request_id: str) -> dict[str, Any]:
        """Create a deterministic pending slot proposal for an existing request."""
        with session_factory() as db:
            try:
                parsed_id = uuid.UUID(request_id)
            except ValueError:
                return {"status": "ERROR", "detail": "Invalid request ID"}
            request = db.get(AppointmentRequest, parsed_id)
            if request is None:
                return {"status": "ERROR", "detail": "Appointment request not found"}
            if request.status != "PENDING_REVIEW":
                return {"status": "ERROR", "detail": "Request is not pending review"}

            proposal = score_and_propose_route(db, request.requested_specialty)
            request.proposed_slot_id = (
                uuid.UUID(proposal["slot_id"]) if proposal["slot_id"] else None
            )
            request.agent_proposal = proposal
            db.add(
                AuditEvent(
                    actor_id=None,
                    action="MCP_SCORE_AND_PROPOSE_ROUTE",
                    entity_type="AppointmentRequest",
                    entity_id=str(request.id),
                    timestamp=datetime.utcnow(),
                    payload=proposal,
                )
            )
            db.commit()
            return proposal

    @server.tool()
    def review_and_commit_tool(approval_token: str) -> dict[str, Any]:
        """Commit a booking or rejection using a short-lived signed clinician approval token."""
        with session_factory() as db:
            try:
                return review_and_commit(db, approval_token)
            except ApprovalError as exc:
                db.rollback()
                return {"status": "ERROR", "detail": str(exc)}

    return server


def main() -> None:
    create_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
