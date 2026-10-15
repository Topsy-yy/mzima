from backend.agent.workflow import AppointmentAgentWorkflow
from backend.db.session import SessionLocal
from backend.models.domain import AppointmentRequest, ClinicianDecision, RoleEnum, User


def test_agent_safety_guardrails():
    db = SessionLocal()
    try:
        print("=== 1. Agent Proposing Booking Slot ===")
        proposal = AppointmentAgentWorkflow.generate_booking_proposal(
            db,
            patient_identifier="P-88301",
            requested_specialty="Orthopedics",
            suggested_slot="2026-10-15T09:00:00Z",
        )
        print(proposal)

        request_id = proposal["request_id"]

        print("\n=== 2. Verifying Safety Invariant (Agent Cannot Auto-Approve) ===")
        is_safe = AppointmentAgentWorkflow.verify_agent_cannot_auto_approve(
            db, request_id
        )
        print(f"Safety Invariant Passed (Status != APPROVED): {is_safe}")

        print("\n=== 3. Simulating Human Clinician Sign-Off ===")
        # Fetch shift lead user seeded in Phase 2
        lead_user = db.query(User).filter(User.role == RoleEnum.SHIFT_LEAD).first()
        req = db.query(AppointmentRequest).filter(AppointmentRequest.id == request_id).first()

        # Human clinician explicitly approves request
        req.status = "APPROVED"
        decision = ClinicianDecision(
            request_id=req.id,
            clinician_id=lead_user.id,
            decision="APPROVE",
            reason="Approved by shift lead after slot verification.",
        )
        db.add(decision)
        db.commit()

        print(f"Final Appointment Request Status: {req.status}")
        print(f"Decision Logged By Clinician ({lead_user.username}): {decision.decision}")

    finally:
        db.close()


if __name__ == "__main__":
    test_agent_safety_guardrails()