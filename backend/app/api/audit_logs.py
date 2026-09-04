"""
Read-only audit log endpoints for RecoverAI.
"""

from fastapi import APIRouter

from app.repositories.entities import get_audit_log_repository


router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
)


@router.get("")
async def list_audit_logs():
    """Return all audit logs."""
    repository = get_audit_log_repository()
    logs = await repository.find_many(limit=100)

    return [log.model_dump(mode="json") for log in logs]