"""Tests for application settings loading."""
import os

import pytest
from pydantic import ValidationError


def test_settings_load_from_env(monkeypatch):
    """All required fields load cleanly from the test env vars."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost/db")
    monkeypatch.setenv("AGENTROUTER_API_KEY", "test-key")
    monkeypatch.setenv("API_SECRET_KEY", "test-secret-32-chars-long-xxxxx")
    monkeypatch.setenv("APPROVAL_TOKEN_SECRET", "test-approval-32-chars-long-xxxx")

    from app.config import Settings
    s = Settings()

    assert s.database_url == "postgresql://u:p@localhost/db"
    assert s.agentrouter_api_key == "test-key"
    assert s.base_url == "https://agentrouter.org/v1"
    assert s.model_name == "claude-opus-4-8"
    assert s.app_env == "development"
    assert isinstance(s.cors_origins, list)


def test_cors_origins_parsed_from_space_separated_string(monkeypatch):
    """CORS origins from a space-separated env string become a list."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost/db")
    monkeypatch.setenv("AGENTROUTER_API_KEY", "key")
    monkeypatch.setenv("API_SECRET_KEY", "secret")
    monkeypatch.setenv("APPROVAL_TOKEN_SECRET", "approval-secret")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000 http://localhost:3001")

    from app.config import Settings
    s = Settings()
    assert s.cors_origins == ["http://localhost:3000", "http://localhost:3001"]


def test_missing_required_field_raises(monkeypatch):
    """Missing DATABASE_URL raises ValidationError."""
    # Remove required vars
    for key in ["DATABASE_URL", "AGENTROUTER_API_KEY", "API_SECRET_KEY", "APPROVAL_TOKEN_SECRET"]:
        monkeypatch.delenv(key, raising=False)

    from app.config import Settings
    with pytest.raises((ValidationError, Exception)):
        Settings()
