"""
Per-entity repository factories for RecoverAI.

All database access should go through these repository factories instead of
accessing MongoDB collections directly from API routes or business logic.

Each factory:
1. Gets the active MongoDB database.
2. Selects the correct collection.
3. Connects that collection to the correct Pydantic domain model.
"""

from __future__ import annotations

from app.db.collections import (
    AI_CONVERSATIONS_COLLECTION,
    AUDIT_LOGS_COLLECTION,
    CUSTOMERS_COLLECTION,
    MERCHANTS_COLLECTION,
    PAYMENT_ATTEMPTS_COLLECTION,
    PAYMENTS_COLLECTION,
    RECOVERY_CASES_COLLECTION,
    DEMO_REQUESTS_COLLECTION,
)
from app.db.mongodb import get_database

from app.models.domain import (
    AIConversation,
    AuditLog,
    Customer,
    Merchant,
    Payment,
    PaymentAttempt,
    RecoveryCase,
    DemoRequest,
)

from app.repositories.base import BaseRepository


def _require_database():
    """
    Return the active MongoDB database.

    Raises:
        RuntimeError: If MongoDB has not been connected.
    """

    database = get_database()

    if database is None:
        raise RuntimeError(
            "MongoDB is not connected. "
            "Set MONGODB_URI in backend/.env, "
            "restart the FastAPI application, "
            "and check GET /api/db/health."
        )

    return database


def get_merchant_repository() -> BaseRepository[Merchant]:
    """Return the repository for merchants."""

    database = _require_database()

    return BaseRepository(
        collection=database[MERCHANTS_COLLECTION],
        model=Merchant,
    )


def get_customer_repository() -> BaseRepository[Customer]:
    """Return the repository for customers."""

    database = _require_database()

    return BaseRepository(
        collection=database[CUSTOMERS_COLLECTION],
        model=Customer,
    )


def get_payment_repository() -> BaseRepository[Payment]:
    """Return the repository for payments."""

    database = _require_database()

    return BaseRepository(
        collection=database[PAYMENTS_COLLECTION],
        model=Payment,
    )


def get_payment_attempt_repository() -> BaseRepository[PaymentAttempt]:
    """Return the repository for payment attempts."""

    database = _require_database()

    return BaseRepository(
        collection=database[PAYMENT_ATTEMPTS_COLLECTION],
        model=PaymentAttempt,
    )


def get_recovery_case_repository() -> BaseRepository[RecoveryCase]:
    """Return the repository for recovery cases."""

    database = _require_database()

    return BaseRepository(
        collection=database[RECOVERY_CASES_COLLECTION],
        model=RecoveryCase,
    )


def get_audit_log_repository() -> BaseRepository[AuditLog]:
    """Return the repository for audit logs."""

    database = _require_database()

    return BaseRepository(
        collection=database[AUDIT_LOGS_COLLECTION],
        model=AuditLog,
    )


def get_ai_conversation_repository() -> BaseRepository[AIConversation]:
    """Return the repository for persistent AI conversations."""

    database = _require_database()

    return BaseRepository(
        collection=database[AI_CONVERSATIONS_COLLECTION],
        model=AIConversation,
    )
    
def get_demo_request_repository() -> BaseRepository[DemoRequest]:
    """Return the repository for demo requests."""

    database = _require_database()

    return BaseRepository(
        collection=database[DEMO_REQUESTS_COLLECTION],
        model=DemoRequest,
    )