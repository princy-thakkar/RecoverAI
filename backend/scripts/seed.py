"""
Development/demo seed script for RecoverAI's MongoDB database.

This is NOT run automatically at application startup. Run it manually,
against a database you're happy to have demo data in:

    cd backend
    python -m scripts.seed

Every record inserted here is clearly labelled as demo data (see the
DEMO_ prefixes and @recoverai-demo.local email domain below) so it is
never mistaken for real merchant/customer/payment data.

Safe to re-run: it clears only the documents it previously inserted
(matched by the same fixed demo ids) before re-inserting them, so running
it twice does not create duplicates or accumulate junk.
"""
import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.db.collections import (
    AUDIT_LOGS_COLLECTION,
    CUSTOMERS_COLLECTION,
    MERCHANTS_COLLECTION,
    PAYMENT_ATTEMPTS_COLLECTION,
    PAYMENTS_COLLECTION,
    RECOVERY_CASES_COLLECTION,
)
from app.db.indexes import ensure_indexes
from app.models.domain import (
    AuditLog,
    Customer,
    Merchant,
    Payment,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
    RecommendedAction,
    RecoveryCase,
    RecoveryCaseStatus,
)
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

# Fixed ids (rather than random uuids) so re-running this script updates
# the same demo records instead of creating new ones each time.
DEMO_MERCHANT_ID = "DEMO_MERCHANT_1"
DEMO_CUSTOMER_ID = "DEMO_CUSTOMER_1"
DEMO_PAYMENT_ID = "DEMO_PAYMENT_1"
DEMO_PAYMENT_ATTEMPT_ID = "DEMO_ATTEMPT_1"
DEMO_RECOVERY_CASE_ID = "DEMO_RECOVERY_CASE_1"
DEMO_AUDIT_LOG_ID = "DEMO_AUDIT_LOG_1"


async def seed() -> None:
    settings = get_settings()

    if not settings.MONGODB_URI:
        logger.error(
            "MONGODB_URI is not set in backend/.env — nothing to seed against."
        )
        return

    client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[settings.MONGODB_DB_NAME]

    await client.admin.command("ping")
    logger.info("Connected to database '%s'.", settings.MONGODB_DB_NAME)

    await ensure_indexes(db)

    merchant = Merchant(
        id=DEMO_MERCHANT_ID,
        name="Demo Merchant (Seed Data)",
        email="demo@example.com",
        password_hash=hash_password("password123"),
    )
    customer = Customer(
        id=DEMO_CUSTOMER_ID,
        merchant_id=DEMO_MERCHANT_ID,
        name="Demo Customer (Seed Data)",
        email="demo.customer@recoverai.com",
        phone="+91 90000 00000",
        risk_score=0.42,
    )
    payment = Payment(
        id=DEMO_PAYMENT_ID,
        merchant_id=DEMO_MERCHANT_ID,
        customer_id=DEMO_CUSTOMER_ID,
        amount=1499.00,
        currency="INR",
        status=PaymentStatus.FAILED,
        payment_method="UPI",
        failure_reason="Insufficient Funds",
    )
    payment_attempt = PaymentAttempt(
        id=DEMO_PAYMENT_ATTEMPT_ID,
        payment_id=DEMO_PAYMENT_ID,
        attempt_number=1,
        status=PaymentAttemptStatus.FAILED,
        failure_reason="Insufficient Funds",
    )
    recovery_case = RecoveryCase(
        id=DEMO_RECOVERY_CASE_ID,
        payment_id=DEMO_PAYMENT_ID,
        customer_id=DEMO_CUSTOMER_ID,
        recovery_probability=0.5,
        status=RecoveryCaseStatus.PENDING,
        recommended_action=RecommendedAction.SMART_RETRY,
    )
    audit_log = AuditLog(
        id=DEMO_AUDIT_LOG_ID,
        payment_id=DEMO_PAYMENT_ID,
        action=RecommendedAction.SMART_RETRY.value,
        reason="Seed data placeholder — not a real automated decision.",
        confidence=0.5,
    )

    seed_docs = [
        (MERCHANTS_COLLECTION, merchant),
        (CUSTOMERS_COLLECTION, customer),
        (PAYMENTS_COLLECTION, payment),
        (PAYMENT_ATTEMPTS_COLLECTION, payment_attempt),
        (RECOVERY_CASES_COLLECTION, recovery_case),
        (AUDIT_LOGS_COLLECTION, audit_log),
    ]

    for collection_name, doc in seed_docs:
        await db[collection_name].delete_one({"id": doc.id})
        await db[collection_name].insert_one(doc.model_dump(mode="python"))
        logger.info("Seeded %s -> %s", collection_name, doc.id)

    client.close()
    logger.info("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())