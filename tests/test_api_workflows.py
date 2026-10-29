from collections.abc import Generator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import get_password_hash
from app.db.session import Base
from app.main import app
from app.models.domain import AppointmentSlot, RoleEnum, User


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with testing_session() as db:
        db.add_all(
            [
                User(
                    username="test-clerk",
                    hashed_password=get_password_hash("test-clerk-password"),
                    role=RoleEnum.CLERK,
                ),
                User(
                    username="test-nurse",
                    hashed_password=get_password_hash("test-nurse-password"),
                    role=RoleEnum.NURSE,
                ),
                User(
                    username="test-clinician",
                    hashed_password=get_password_hash("test-clinician-password"),
                    role=RoleEnum.SHIFT_LEAD,
                ),
            ]
        )
        db.add(
            AppointmentSlot(
                specialty="General outpatient",
                starts_at=datetime.utcnow() + timedelta(days=1),
                capacity=1,
                booked_count=0,
            )
        )
        db.commit()

    def override_get_db() -> Generator:
        with testing_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def access_token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_request(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/appointments/appointment-requests",
        json={
            "patient_identifier": "DEMO-REQ-100",
            "requested_specialty": "General outpatient",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_patient_request_is_visible_only_in_authenticated_staff_inbox(
    client: TestClient,
) -> None:
    request = create_request(client)
    assert request["status"] == "PENDING_REVIEW"
    assert request["agent_proposal"]["tool"] == "score_and_propose_route"
    assert request["agent_proposal"]["status"] == "PENDING_CLINICIAN_REVIEW"
    assert request["proposed_slot_id"]
    assert request["booked_slot_id"] is None

    assert client.get("/api/v1/appointments/clinic/review-queue").status_code == 401
    assert client.get(f"/api/v1/appointments/appointments/{request['id']}").status_code == 401

    token = access_token(client, "test-clinician", "test-clinician-password")
    response = client.get("/api/v1/appointments/clinic/review-queue", headers=bearer(token))
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [request["id"]]


@pytest.mark.parametrize(
    ("decision", "status"),
    [("APPROVE", "BOOKED"), ("REJECT", "REJECTED")],
)
def test_clinician_decision_requires_reason_is_audited_and_cannot_repeat(
    client: TestClient,
    decision: str,
    status: str,
) -> None:
    request = create_request(client)
    token = access_token(client, "test-clinician", "test-clinician-password")
    path = f"/api/v1/appointments/appointment-requests/{request['id']}/decision"

    invalid = client.post(
        path,
        headers=bearer(token),
        json={"decision": "MODIFY", "reason": "Need edit"},
    )
    assert invalid.status_code == 422

    response = client.post(
        path,
        headers=bearer(token),
        json={"decision": decision, "reason": "Reviewed synthetic request"},
    )
    assert response.status_code == 200
    assert response.json()["decision"] == decision
    assert response.json()["reason"] == "Reviewed synthetic request"

    details = client.get(
        f"/api/v1/appointments/appointments/{request['id']}",
        headers=bearer(token),
    )
    assert details.status_code == 200
    assert details.json()["status"] == status
    assert (details.json()["booked_slot_id"] is not None) == (decision == "APPROVE")

    repeated = client.post(
        path,
        headers=bearer(token),
        json={"decision": "APPROVE", "reason": "Second attempt"},
    )
    assert repeated.status_code == 409


def test_approval_fails_when_request_has_no_matching_slot(client: TestClient) -> None:
    request = client.post(
        "/api/v1/appointments/appointment-requests",
        json={
            "patient_identifier": "DEMO-NO-SLOT",
            "requested_specialty": "Unavailable service",
        },
    ).json()
    token = access_token(client, "test-clinician", "test-clinician-password")
    response = client.post(
        f"/api/v1/appointments/appointment-requests/{request['id']}/decision",
        headers=bearer(token),
        json={"decision": "APPROVE", "reason": "Test no-match guard"},
    )
    assert response.status_code == 409
    details = client.get(
        f"/api/v1/appointments/appointments/{request['id']}", headers=bearer(token)
    )
    assert details.json()["status"] == "PENDING_REVIEW"
    assert details.json()["booked_slot_id"] is None


def test_stale_slot_proposal_cannot_overbook_capacity(client: TestClient) -> None:
    first = create_request(client)
    second = create_request(client)
    assert first["proposed_slot_id"] == second["proposed_slot_id"]
    token = access_token(client, "test-clinician", "test-clinician-password")

    for request in (first, second):
        response = client.post(
            f"/api/v1/appointments/appointment-requests/{request['id']}/decision",
            headers=bearer(token),
            json={"decision": "APPROVE", "reason": "Synthetic capacity evaluation"},
        )
        if request is first:
            assert response.status_code == 200
        else:
            assert response.status_code == 409
            details = client.get(
                f"/api/v1/appointments/appointments/{request['id']}",
                headers=bearer(token),
            )
            assert details.json()["status"] == "PENDING_REVIEW"
            assert details.json()["booked_slot_id"] is None


def test_walk_in_queue_check_in_call_and_triage_are_role_protected(
    client: TestClient,
) -> None:
    clerk_token = access_token(client, "test-clerk", "test-clerk-password")
    nurse_token = access_token(client, "test-nurse", "test-nurse-password")

    assert client.get("/api/v1/queue").status_code == 401
    unauthorized = client.post(
        "/api/v1/visits",
        headers=bearer(nurse_token),
        json={"age_band": "adult", "visit_type": "new", "red_flags": {}},
    )
    assert unauthorized.status_code == 403

    check_in = client.post(
        "/api/v1/visits",
        headers=bearer(clerk_token),
        json={"age_band": "adult", "visit_type": "new", "red_flags": {}},
    )
    assert check_in.status_code == 200
    visit = check_in.json()

    queue = client.get("/api/v1/queue", headers=bearer(nurse_token))
    assert queue.status_code == 200
    assert queue.json()[0]["visit_id"] == visit["id"]

    call = client.post(
        f"/api/v1/queue/{visit['id']}/call",
        headers=bearer(nurse_token),
        json={"override_reason": None},
    )
    assert call.status_code == 200
    assert call.json()["status"] == "called"

    triage = client.post(
        f"/api/v1/visits/{visit['id']}/triage",
        headers=bearer(nurse_token),
        json={"triage_category": "Green", "destination": "Consultation"},
    )
    assert triage.status_code == 200
    assert triage.json()["status"] == "triaged"


def test_patient_request_rejects_blank_or_oversized_values(client: TestClient) -> None:
    blank = client.post(
        "/api/v1/appointments/appointment-requests",
        json={"patient_identifier": "  ", "requested_specialty": "General"},
    )
    assert blank.status_code == 422

    too_long = client.post(
        "/api/v1/appointments/appointment-requests",
        json={
            "patient_identifier": "D" * 101,
            "requested_specialty": "General",
        },
    )
    assert too_long.status_code == 422
