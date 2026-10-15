from fastapi import APIRouter
from app.api.v1.endpoints import appointments, auth, flow, queue

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(queue.router, tags=["walk-in queue"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(flow.router, tags=["flow optimisation"])