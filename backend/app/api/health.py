"""Health check endpoint — used for uptime checks and to confirm the
frontend can reach the backend."""
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health():
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }