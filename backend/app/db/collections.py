"""
MongoDB collection name constants for RecoverAI.

All MongoDB collection names are defined in one place so repositories,
index setup, seed scripts, and API code use the same names.
"""

from __future__ import annotations


MERCHANTS_COLLECTION = "merchants"

CUSTOMERS_COLLECTION = "customers"

PAYMENTS_COLLECTION = "payments"

PAYMENT_ATTEMPTS_COLLECTION = "payment_attempts"

RECOVERY_CASES_COLLECTION = "recovery_cases"

AUDIT_LOGS_COLLECTION = "audit_logs"

AI_CONVERSATIONS_COLLECTION = "ai_conversations"

DEMO_REQUESTS_COLLECTION = "demo_requests"
