import asyncio
import json
from typing import Any

import httpx
from mcp import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session
from sqlalchemy.orm import Session

from app.core.config import settings
from app.mcp.server import create_mcp_server


ALLOWED_MODEL_TOOLS = {"get_appointment_slots_tool", "score_and_propose_route_tool"}


class LocalAgentError(Exception):
    pass


def _mcp_result_value(result: Any) -> dict[str, Any]:
    if result.isError:
        raise LocalAgentError("MCP tool returned an error")
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
    raise LocalAgentError("MCP tool returned no structured result")


async def run_local_agent(
    request_id: str,
    requested_specialty: str,
    session_factory,
) -> dict[str, Any]:
    if not settings.LOCAL_MODEL_NAME:
        raise LocalAgentError("LOCAL_MODEL_NAME is required when the local agent is enabled")

    server = create_mcp_server(session_factory)
    async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            listed = await session.list_tools()
            exposed = [tool for tool in listed.tools if tool.name in ALLOWED_MODEL_TOOLS]
            model_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in exposed
            ]
            if {tool["function"]["name"] for tool in model_tools} != ALLOWED_MODEL_TOOLS:
                raise LocalAgentError("Required read/proposal MCP tools are unavailable")

            messages: list[dict[str, Any]] = [
                {
                    "role": "system",
                    "content": (
                        "You are a bounded synthetic appointment assistant. Use only the provided tools "
                        "to check this requested service and create a pending slot proposal. Never book, "
                        "approve, infer diagnosis, urgency, or clinical priority. Do not invent tool outputs."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "request_id": request_id,
                            "requested_specialty": requested_specialty,
                            "task": "Check available slots, then create a pending proposal.",
                        }
                    ),
                },
            ]

            async with httpx.AsyncClient(
                base_url=settings.LOCAL_MODEL_BASE_URL.rstrip("/"),
                timeout=settings.LOCAL_MODEL_TIMEOUT_SECONDS,
                headers={"Authorization": f"Bearer {settings.LOCAL_MODEL_API_KEY}"},
            ) as client:
                for _ in range(3):
                    response = await client.post(
                        "/chat/completions",
                        json={
                            "model": settings.LOCAL_MODEL_NAME,
                            "messages": messages,
                            "tools": model_tools,
                            "tool_choice": "auto",
                            "temperature": 0,
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    message = payload["choices"][0]["message"]
                    tool_calls = message.get("tool_calls") or []
                    if not tool_calls:
                        break
                    messages.append(message)
                    for tool_call in tool_calls:
                        function = tool_call.get("function", {})
                        name = function.get("name")
                        if name not in ALLOWED_MODEL_TOOLS:
                            raise LocalAgentError("Model requested a tool outside the allowlist")
                        arguments = json.loads(function.get("arguments") or "{}")
                        if name == "get_appointment_slots_tool":
                            arguments = {"specialty": requested_specialty}
                        elif name == "score_and_propose_route_tool":
                            arguments = {"request_id": request_id}
                        tool_result = await session.call_tool(name, arguments)
                        value = _mcp_result_value(tool_result)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps(value),
                            }
                        )
                        if name == "score_and_propose_route_tool":
                            return value

    raise LocalAgentError("Local model did not create a pending proposal")


def run_local_agent_sync(
    request_id: str,
    requested_specialty: str,
    session_factory,
) -> dict[str, Any]:
    return asyncio.run(run_local_agent(request_id, requested_specialty, session_factory))


async def commit_via_mcp(
    approval_token: str,
    session_factory,
) -> dict[str, Any]:
    server = create_mcp_server(session_factory)
    async with create_connected_server_and_client_session(server) as session:
        await session.initialize()
        result = await session.call_tool(
            "review_and_commit_tool", {"approval_token": approval_token}
        )
        return _mcp_result_value(result)


def commit_via_mcp_sync(approval_token: str, session_factory) -> dict[str, Any]:
    return asyncio.run(commit_via_mcp(approval_token, session_factory))
