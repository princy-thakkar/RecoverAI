"""Database health endpoint — reports whether MongoDB is reachable.

Separate from GET /api/health (Stage 1), which only confirms the API
process itself is up. This endpoint answers a different question: is the
database dependency available right now.
"""
from fastapi import APIRouter

from app.db.mongodb import check_db_health

router = APIRouter(tags=["database"])


@router.get("/db/health")
async def get_db_health():
    result = await check_db_health()
    return {
        "database": "mongodb",
        **result,
    }