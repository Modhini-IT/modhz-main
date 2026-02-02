"""
Main API router for v1 endpoints
"""
from fastapi import APIRouter

from app.api.v1.endpoints import students, attendance, recognition, training

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(recognition.router, prefix="/recognition", tags=["recognition"])
api_router.include_router(training.router, prefix="/training", tags=["training"])