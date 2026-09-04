"""
MongoDB connection lifecycle for RecoverAI.

This module owns the single Motor client and database instance used by
the FastAPI application.

Routes and business logic should NOT access Motor directly.
They should use repositories from app.repositories.

If MONGODB_URI is not configured, the application can still start, but
database-backed endpoints will report MongoDB as unavailable.
"""

from __future__ import annotations

import logging

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
)

from app.core.config import get_settings
from app.db.indexes import ensure_indexes


logger = logging.getLogger(__name__)


class MongoDB:
    """
    Process-wide MongoDB connection state.

    `client` contains the Motor client.
    `db` contains the selected application database.
    """

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongodb = MongoDB()


async def connect_to_mongo() -> None:
    """
    Connect to MongoDB during application startup.

    The function intentionally does not crash the FastAPI application
    when MongoDB is unavailable. The database health endpoint can report
    the problem instead.
    """

    settings = get_settings()

    # ---------------------------------------------------------
    # MongoDB is not configured
    # ---------------------------------------------------------

    if not settings.MONGODB_URI:
        logger.warning(
            "MONGODB_URI is not configured. "
            "Starting RecoverAI without MongoDB."
        )

        mongodb.client = None
        mongodb.db = None

        return

    # ---------------------------------------------------------
    # Clean up any previous connection
    # ---------------------------------------------------------

    if mongodb.client is not None:
        try:
            mongodb.client.close()
        except Exception:
            pass

        mongodb.client = None
        mongodb.db = None

    # ---------------------------------------------------------
    # Create MongoDB client
    # ---------------------------------------------------------

    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
        )

        database = client[settings.MONGODB_DB_NAME]

        # -----------------------------------------------------
        # Verify the connection
        # -----------------------------------------------------

        await client.admin.command("ping")

        # -----------------------------------------------------
        # Store active connection
        # -----------------------------------------------------

        mongodb.client = client
        mongodb.db = database

        logger.info(
            "Connected to MongoDB database '%s'.",
            settings.MONGODB_DB_NAME,
        )

        # -----------------------------------------------------
        # Ensure indexes
        # -----------------------------------------------------

        await ensure_indexes(database)

        logger.info("MongoDB indexes verified successfully.")

    except Exception as exc:
        logger.error(
            "Failed to connect to MongoDB: %s",
            exc,
        )

        # Make absolutely sure repositories cannot use
        # a partially initialized connection.

        try:
            client.close()
        except Exception:
            pass

        mongodb.client = None
        mongodb.db = None


async def close_mongo_connection() -> None:
    """
    Close the MongoDB connection during application shutdown.
    """

    if mongodb.client is None:
        return

    try:
        mongodb.client.close()

        logger.info(
            "MongoDB connection closed."
        )

    except Exception as exc:
        logger.error(
            "Error while closing MongoDB connection: %s",
            exc,
        )

    finally:
        mongodb.client = None
        mongodb.db = None


def get_database() -> AsyncIOMotorDatabase | None:
    """
    Return the currently connected MongoDB database.

    Returns:
        AsyncIOMotorDatabase:
            When MongoDB is connected.

        None:
            When MongoDB is not configured or connection failed.
    """

    return mongodb.db


async def check_db_health() -> dict:
    """
    Check whether MongoDB is currently reachable.

    This performs a real ping instead of relying only on the cached
    connection state.
    """

    settings = get_settings()

    # ---------------------------------------------------------
    # MongoDB configuration check
    # ---------------------------------------------------------

    if not settings.MONGODB_URI:
        return {
            "connected": False,
            "database": "mongodb",
            "detail": (
                "MongoDB is not configured. "
                "Set MONGODB_URI in backend/.env."
            ),
        }

    # ---------------------------------------------------------
    # Client initialization check
    # ---------------------------------------------------------

    if mongodb.client is None:
        return {
            "connected": False,
            "database": "mongodb",
            "detail": (
                "MongoDB client failed to initialize. "
                "Check the backend logs and MongoDB configuration."
            ),
        }

    # ---------------------------------------------------------
    # Live connection check
    # ---------------------------------------------------------

    try:
        await mongodb.client.admin.command("ping")

        return {
            "connected": True,
            "database": "mongodb",
            "detail": (
                f"Connected to database "
                f"'{settings.MONGODB_DB_NAME}'."
            ),
        }

    except Exception as exc:
        logger.error(
            "MongoDB health check failed: %s",
            exc,
        )

        return {
            "connected": False,
            "database": "mongodb",
            "detail": (
                f"MongoDB ping failed: {exc}"
            ),
        }