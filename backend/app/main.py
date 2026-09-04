"""
RecoverAI FastAPI application entrypoint.

Provides:
- FastAPI application bootstrap
- CORS
- MongoDB lifecycle
- health endpoints
- authentication
- dashboard
- analytics
- payments
- customers
- recovery
- ML
- AI
- payment attempts
- audit logs
- settings
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    ai,
    analytics,
    audit_logs,
    auth,
    customers,
    dashboard,
    db_health,
    health,
    ml,
    payment_attempts,
    payments,
    recovery_cases,
    settings as settings_api,
)
from app.api.benchmark import router as benchmark_router
from app.core.config import get_settings
from app.db.mongodb import (
    close_mongo_connection,
    connect_to_mongo,
)
from app.db.seed import seed_demo_merchant


settings = get_settings()
logger = logging.getLogger(__name__)


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Connect to MongoDB when the application starts,
    ensure the demo merchant exists, and close the
    connection when the application shuts down.
    """

    # Connect to MongoDB
    await connect_to_mongo()

    # Create the demo merchant if it does not already exist.
    #
    # This allows a fresh evaluator environment to log into
    # the frontend without manually registering an account.
    try:
        await seed_demo_merchant()
    except Exception as exc:
        logger.error(
            "Failed to seed demo merchant: %s",
            exc,
        )

    # Application runs
    yield

    # Close MongoDB connection on shutdown
    await close_mongo_connection()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered revenue recovery platform — "
        "backend API."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

# ------------------------------------------------------------
# Health
# ------------------------------------------------------------

app.include_router(
    health.router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    db_health.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Authentication
# ------------------------------------------------------------

app.include_router(
    auth.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------

app.include_router(
    dashboard.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Analytics
# ------------------------------------------------------------

app.include_router(
    analytics.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Payments
# ------------------------------------------------------------

app.include_router(
    payments.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Customers
# ------------------------------------------------------------

app.include_router(
    customers.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Recovery Cases
# ------------------------------------------------------------

app.include_router(
    recovery_cases.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# ML
# ------------------------------------------------------------

app.include_router(
    ml.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# AI
# ------------------------------------------------------------

app.include_router(
    ai.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Payment Attempts
# ------------------------------------------------------------

app.include_router(
    payment_attempts.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Audit Logs
# ------------------------------------------------------------

app.include_router(
    audit_logs.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Settings
# ------------------------------------------------------------

app.include_router(
    settings_api.router,
    prefix=settings.API_PREFIX,
)


# ------------------------------------------------------------
# Benchmark
# ------------------------------------------------------------

app.include_router(
    benchmark_router,
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": (
            "RecoverAI API is running. "
            "See /docs for API documentation."
        )
    }