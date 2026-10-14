from __future__ import annotations

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Mzima Backend"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    DEBUG: bool = True

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "mzima_user"
    POSTGRES_PASSWORD: str = "asdf"
    POSTGRES_DB: str = "mzima_db"
    DATABASE_URL: str = "postgresql://mzima_user:asdf@localhost:5432/mzima_db"

    # Security, with compatibility for the consolidated environment style.
    SECRET_KEY: str = ""
    API_SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    JWT_ALGORITHM: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    JWT_EXPIRE_MINUTES: int | None = None

    # Agent Router; BASE_URL and MODEL_NAME are accepted for the consolidated style.
    AGENTROUTER_API_KEY: str = ""
    BASE_URL: str | None = None
    AGENTROUTER_BASE_URL: str = "https://agentrouter.org"
    MODEL_NAME: str | None = None
    AGENTROUTER_MODEL: str = "gpt-4o-mini"
    AGENTROUTER_TIMEOUT_SECONDS: int = 30

    APP_ENV: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    @model_validator(mode="after")
    def resolve_aliases(self):
        if not self.SECRET_KEY and self.API_SECRET_KEY:
            self.SECRET_KEY = self.API_SECRET_KEY
        if not self.SECRET_KEY:
            self.SECRET_KEY = "dev_secret_key_change_in_production"
        if self.JWT_ALGORITHM:
            self.ALGORITHM = self.JWT_ALGORITHM
        if self.JWT_EXPIRE_MINUTES is not None:
            self.ACCESS_TOKEN_EXPIRE_MINUTES = self.JWT_EXPIRE_MINUTES
        if self.BASE_URL:
            self.AGENTROUTER_BASE_URL = self.BASE_URL.rstrip("/")
        if self.MODEL_NAME:
            self.AGENTROUTER_MODEL = self.MODEL_NAME
        if self.APP_ENV:
            self.ENV = self.APP_ENV
        return self


settings = Settings()
