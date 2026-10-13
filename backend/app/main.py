"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: DB pool and other resources will be initialised here in later tasks
    logger.info("Mzima API starting up (env=%s)", get_settings().app_env)
    yield
    # Shutdown: release resources
    logger.info("Mzima API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Mzima API",
        description="Outpatient flow optimisation — appointment routing co-pilot",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers registered here as they are built
    from app.api import appointments  # noqa: PLC0415
    app.include_router(appointments.router, prefix="/api")

    return app


app = create_app()


@app.get("/", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "mzima-api"}
