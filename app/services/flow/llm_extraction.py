"""Optional assistive extraction using an OpenAI-compatible AgentRouter endpoint.

This is used only to convert free text into structured fields. It is not allowed to
diagnose, assign priority, or produce safety-critical recommendations.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from app.core.config import settings


def extract_observation_fields(text: str) -> dict[str, Any]:
    if not settings.AGENTROUTER_API_KEY:
        raise RuntimeError("AGENTROUTER_API_KEY is not configured")

    base = settings.AGENTROUTER_BASE_URL.rstrip("/")
    if base.endswith("/v1"):
        url = base + "/chat/completions"
    else:
        url = base + "/v1/chat/completions"

    system_prompt = (
        "Extract possible clinical observation fields from the supplied text. "
        "Return JSON only. Do not diagnose. Do not assign priority. "
        "Use null for unknown values. Allowed keys: temperature_c, pulse_bpm, respiratory_rate, "
        "oxygen_saturation, capillary_refill_seconds, systolic_bp, diastolic_bp, avpu, "
        "severe_pallor, reported_symptoms, symptom_summary."
    )
    payload = {
        "model": settings.AGENTROUTER_MODEL,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.AGENTROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.AGENTROUTER_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"AgentRouter request failed: {exc}") from exc

    content = data["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError("Model did not return a JSON object")
    parsed = json.loads(match.group(0))
    allowed = {
        "temperature_c",
        "pulse_bpm",
        "respiratory_rate",
        "oxygen_saturation",
        "capillary_refill_seconds",
        "systolic_bp",
        "diastolic_bp",
        "avpu",
        "severe_pallor",
        "reported_symptoms",
        "symptom_summary",
    }
    return {key: value for key, value in parsed.items() if key in allowed}
