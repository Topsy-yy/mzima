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

    # AgentRouter is for prototype/synthetic-data use only.
    AGENTROUTER_API_KEY: str = ""
    AGENTROUTER_BASE_URL: str = "https://agentrouter.org"
    AGENTROUTER_MODEL: str = "gpt-4o-mini"
    AGENTROUTER_TIMEOUT_SECONDS: int = 30

    SECRET_KEY: str = "dev_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480


    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()