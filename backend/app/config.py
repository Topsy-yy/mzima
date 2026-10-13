"""Application settings loaded from environment variables."""
import json
from functools import lru_cache
from typing import Any

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str
    # LLM gateway
    agentrouter_api_key: str
    base_url: str = "https://agentrouter.org/v1"
    model_name: str = "claude-opus-4-8"
    # API auth
    api_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    # App
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    # Clinician approval gate
    approval_token_secret: str
    approval_token_expire_seconds: int = 300
    # Audit
    audit_log_path: str = "./logs/audit.jsonl"
    # Clinic adapter
    clinic_adapter_url: str = "http://localhost:8001"

    @model_validator(mode="before")
    @classmethod
    def _parse_cors_origins(cls, data: Any) -> Any:
        """pydantic-settings passes raw env values here before JSON decoding.
        Handle space-separated strings like 'http://a http://b'."""
        if isinstance(data, dict) and "cors_origins" in data:
            v = data["cors_origins"]
            if isinstance(v, str):
                # Try JSON first (handles '["a","b"]'), fall back to space-split
                stripped = v.strip()
                if stripped.startswith("["):
                    try:
                        data["cors_origins"] = json.loads(stripped)
                    except json.JSONDecodeError:
                        data["cors_origins"] = [o.strip() for o in stripped.split() if o.strip()]
                else:
                    data["cors_origins"] = [o.strip() for o in stripped.split() if o.strip()]
        return data


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — call this everywhere instead of Settings()."""
    return Settings()
