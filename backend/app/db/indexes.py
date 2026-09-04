"""
MongoDB index definitions for RecoverAI.

This module creates all indexes required by the application's
MongoDB collections.

`ensure_indexes()` is called after a successful MongoDB connection.
MongoDB safely handles indexes that already exist, so this function
can run every time the application starts.
"""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import (
    AI_CONVERSATIONS_COLLECTION,
    AUDIT_LOGS_COLLECTION,
    CUSTOMERS_COLLECTION,
    MERCHANTS_COLLECTION,
    PAYMENT_ATTEMPTS_COLLECTION,
    PAYMENTS_COLLECTION,
    RECOVERY_CASES_COLLECTION,
)


logger = logging.getLogger(__name__)


async def ensure_indexes(
    db: AsyncIOMotorDatabase,
) -> None:
    """
    Create all required MongoDB indexes for RecoverAI.

    Indexes improve lookup performance and enforce uniqueness where
    required by the domain model.
    """

    # =========================================================
    # MERCHANTS
    # =========================================================

    await db[
        MERCHANTS_COLLECTION
    ].create_index(
        "id",
        unique=True,
    )

    await db[
        MERCHANTS_COLLECTION
    ].create_index(
        "email",
        unique=True,
    )

    await db[
        MERCHANTS_COLLECTION
    ].create_index(
        "created_at",
    )

    # =========================================================
    # CUSTOMERS
    # =========================================================

    await db[
        CUSTOMERS_COLLECTION
    ].create_index(
        "id",
        unique=True,
    )

    await db[
        CUSTOMERS_COLLECTION
    ].create_index(
        "merchant_id",
    )

    await db[
        CUSTOMERS_COLLECTION
    ].create_index(
        "created_at",
    )

    # =========================================================
    # PAYMENTS
    # =========================================================

    await db[
        PAYMENTS_COLLECTION
    ].create_index(
        "id",
        unique=True,
    )

    await db[
        PAYMENTS_COLLECTION
    ].create_index(
        "merchant_id",
    )

    await db[
        PAYMENTS_COLLECTION
    ].create_index(
        "customer_id",
    )

    await db[
        PAYMENTS_COLLECTION
    ].create_index(
        "status",
    )

    await db[
        PAYMENTS_COLLECTION
    ].create_index(
        "created_at",
    )

    # =========================================================
    # PAYMENT ATTEMPTS
    # =========================================================

    await db[
        PAYMENT_ATTEMPTS_COLLECTION
    ].create_index(
        "id",
        unique=True,
    )

    await db[
        PAYMENT_ATTEMPTS_COLLECTION
    ].create_index(
        "payment_id",
    )

    await db[
        PAYMENT_ATTEMPTS_COLLECTION
    ].create_index(
        "status",
    )

    await db[
        PAYMENT_ATTEMPTS_COLLECTION
    ].create_index(
        "attempted_at",
    )

    # =========================================================
    # RECOVERY CASES
    # =========================================================

    await db[
        RECOVERY_CASES_COLLECTION
    ].create_index(
        "id",
        unique=True,
    )

    await db[
        RECOVERY_CASES_COLLECTION
    ].create_index(
        "payment_id",
    )

    await db[
        RECOVERY_CASES_COLLECTION
    ].create_index(
        "customer_id",
    )

    await db[
        RECOVERY_CASES_COLLECTION
    ].create_index(
        "status",
    )

    await db[
        RECOVERY_CASES_COLLECTION
    ].create_index(
        "created_at",
    )

    # =========================================================
    # AUDIT LOGS
    # =========================================================

    await db[
        AUDIT_LOGS_COLLECTION
    ].create_index(
        "id",
        unique=True,
    )

    await db[
        AUDIT_LOGS_COLLECTION
    ].create_index(
        "payment_id",
    )

    await db[
        AUDIT_LOGS_COLLECTION
    ].create_index(
        "created_at",
    )

    # =========================================================
    # AI CONVERSATIONS
    # =========================================================

    await db[
        AI_CONVERSATIONS_COLLECTION
    ].create_index(
        "id",
        unique=True,
    )

    await db[
        AI_CONVERSATIONS_COLLECTION
    ].create_index(
        "merchant_id",
    )

    await db[
        AI_CONVERSATIONS_COLLECTION
    ].create_index(
        "updated_at",
    )

    # =========================================================
    # COMPLETE
    # =========================================================

    logger.info(
        "MongoDB indexes ensured for all RecoverAI collections."
    )