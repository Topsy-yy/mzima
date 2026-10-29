import secrets
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Mzima Backend"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    DEBUG: bool = True

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "mzima_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "mzima_db"
    DATABASE_URL: str = "sqlite:///./mzima.db"

    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    LOCAL_AGENT_ENABLED: bool = False
    LOCAL_MODEL_BASE_URL: str = "http://127.0.0.1:11434/v1"
    LOCAL_MODEL_NAME: str = ""
    LOCAL_MODEL_API_KEY: str = "local"
    LOCAL_MODEL_TIMEOUT_SECONDS: float = 20.0

    @field_validator("LOCAL_MODEL_BASE_URL")
    @classmethod
    def require_loopback_model_endpoint(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ValueError("LOCAL_MODEL_BASE_URL must use a loopback host")
        return value.rstrip("/")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
