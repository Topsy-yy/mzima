import asyncio
from datetime import datetime, timedelta

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import Base
from app.mcp.server import create_mcp_server
from app.models.domain import AppointmentRequest, AppointmentSlot, RoleEnum, User
from app.services.appointments import local_agent
from app.services.appointments.local_agent import _mcp_result_value
from app.services.appointments.workflow import issue_approval_token


@pytest.fixture
def mcp_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    with testing_session() as db:
        clinician = User(
            username="mcp-clinician",
            hashed_password=get_password_hash("mcp-test-password"),
            role=RoleEnum.SHIFT_LEAD,
            is_active=True,
        )
        slot = AppointmentSlot(
            specialty="General outpatient",
            starts_at=datetime.utcnow() + timedelta(days=1),
            capacity=1,
            booked_count=0,
        )
        db.add_all([clinician, slot])
        db.flush()
        request = AppointmentRequest(
            patient_identifier="SYNTHETIC-AGENT-01",
            requested_specialty="General outpatient",
            status="PENDING_REVIEW",
            proposed_slot_id=slot.id,
            agent_proposal={"tool": "score_and_propose_route", "status": "PENDING_CLINICIAN_REVIEW"},
        )
        db.add(request)
        db.commit()
        request_id = str(request.id)
        clinician_id = clinician.id

    yield testing_session, request_id, clinician_id
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_mcp_tools_commit_only_with_valid_approval_and_reject_replay(mcp_database) -> None:
    testing_session, request_id, clinician_id = mcp_database
    approval_token = issue_approval_token(
        request_id=__import__("uuid").UUID(request_id),
        clinician_id=clinician_id,
        decision="APPROVE",
        reason="Synthetic MCP integration test",
    )

    async def exercise_mcp() -> None:
        server = create_mcp_server(testing_session)
        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "get_appointment_slots_tool",
                "score_and_propose_route_tool",
                "review_and_commit_tool",
            }
            available = await session.call_tool(
                "get_appointment_slots_tool", {"specialty": "General outpatient"}
            )
            assert _mcp_result_value(available)["slots"]

            committed = await session.call_tool(
                "review_and_commit_tool", {"approval_token": approval_token}
            )
            assert _mcp_result_value(committed)["status"] == "BOOKED"

            replayed = await session.call_tool(
                "review_and_commit_tool", {"approval_token": approval_token}
            )
            assert _mcp_result_value(replayed)["status"] == "ERROR"

    asyncio.run(exercise_mcp())
    with testing_session() as db:
        saved_request = db.get(AppointmentRequest, __import__("uuid").UUID(request_id))
        assert saved_request.status == "BOOKED"
        slot = db.get(AppointmentSlot, saved_request.booked_slot_id)
        assert slot.booked_count == 1


def test_local_agent_limits_model_to_read_and_proposal_tools(mcp_database, monkeypatch) -> None:
    testing_session, request_id, _ = mcp_database
    monkeypatch.setattr(settings, "LOCAL_MODEL_NAME", "synthetic-test-model")
    responses = [
        {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call-slots",
                                "function": {
                                    "name": "get_appointment_slots_tool",
                                    "arguments": '{"specialty":"untrusted value"}',
                                },
                            }
                        ]
                    }
                }
            ]
        },
        {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call-proposal",
                                "function": {
                                    "name": "score_and_propose_route_tool",
                                    "arguments": '{"request_id":"untrusted value"}',
                                },
                            }
                        ]
                    }
                }
            ]
        },
    ]
    observed_requests = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, path, json):
            observed_requests.append(json)
            return FakeResponse(responses.pop(0))

    monkeypatch.setattr(local_agent.httpx, "AsyncClient", FakeAsyncClient)
    proposal = local_agent.run_local_agent_sync(
        request_id,
        "General outpatient",
        testing_session,
    )

    assert proposal["status"] == "PENDING_CLINICIAN_REVIEW"
    assert len(observed_requests) == 2
    assert {tool["function"]["name"] for tool in observed_requests[0]["tools"]} == {
        "get_appointment_slots_tool",
        "score_and_propose_route_tool",
    }
    assert "review_and_commit_tool" not in str(observed_requests[0]["tools"])
    assert "SYNTHETIC-AGENT-01" not in str(observed_requests)
