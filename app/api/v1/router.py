from fastapi import APIRouter
<<<<<<< Updated upstream:app/api/v1/router.py
from app.api.v1.endpoints import appointments, auth, flow, queue
=======
from backend.api.v1.endpoints import appointments, auth, queue
>>>>>>> Stashed changes:backend/api/v1/router.py

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(queue.router, tags=["walk-in queue"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(flow.router, tags=["flow optimisation"])