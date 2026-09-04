from __future__ import annotations

import logging

from app.core.security import hash_password
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
from app.repositories.entities import (
    get_audit_log_repository,
    get_customer_repository,
    get_merchant_repository,
    get_payment_attempt_repository,
    get_payment_repository,
    get_recovery_case_repository,
)

logger = logging.getLogger(__name__)

# ============================================================
# CANONICAL DEMO DATA
# ============================================================

DEMO_MERCHANT_ID = "DEMO_MERCHANT_1"
DEMO_CUSTOMER_ID = "DEMO_CUSTOMER_1"
DEMO_PAYMENT_ID = "DEMO_PAYMENT_1"
DEMO_PAYMENT_ATTEMPT_ID = "DEMO_ATTEMPT_1"
DEMO_RECOVERY_CASE_ID = "DEMO_RECOVERY_CASE_1"
DEMO_AUDIT_LOG_ID = "DEMO_AUDIT_LOG_1"

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "password123"
DEMO_NAME = "Demo Merchant"


# ============================================================
# STARTUP DEMO SEED
# ============================================================

async def seed_demo_merchant() -> None:
    """
    Ensure the canonical RecoverAI demo environment exists.

    This function is called automatically during FastAPI startup.

    It is intentionally idempotent:
    - existing demo records are preserved;
    - missing demo records are created;
    - evaluator recovery actions are not reset on server restart;
    - all demo data belongs to DEMO_MERCHANT_1.
    """

    merchant_repository = get_merchant_repository()

    # --------------------------------------------------------
    # 1. Ensure the canonical demo merchant exists.
    # --------------------------------------------------------

    canonical_merchant = await merchant_repository.find_by_id(
        DEMO_MERCHANT_ID,
    )

    if canonical_merchant is not None:
        # Auth searches by email, so remove legacy records that
        # could otherwise authenticate as a different merchant.
        merchants_with_demo_email = await merchant_repository.find_many(
            {
                "email": DEMO_EMAIL,
            },
            limit=100,
        )

        for merchant in merchants_with_demo_email:
            if merchant.id != DEMO_MERCHANT_ID:
                await merchant_repository.delete_by_id(
                    merchant.id,
                )

                logger.info(
                    "Removed legacy demo merchant: %s",
                    merchant.id,
                )

        # Keep the canonical demo credentials valid.
        await merchant_repository.update_by_id(
            DEMO_MERCHANT_ID,
            {
                "name": DEMO_NAME,
                "email": DEMO_EMAIL,
                "password_hash": hash_password(
                    DEMO_PASSWORD,
                ),
            },
        )

        logger.info(
            "Canonical demo merchant ready: %s (%s)",
            DEMO_EMAIL,
            DEMO_MERCHANT_ID,
        )

    else:
        # Remove any old merchant using the canonical demo email.
        merchants_with_demo_email = await merchant_repository.find_many(
            {
                "email": DEMO_EMAIL,
            },
            limit=100,
        )

        for merchant in merchants_with_demo_email:
            await merchant_repository.delete_by_id(
                merchant.id,
            )

            logger.info(
                "Removed legacy demo merchant: %s",
                merchant.id,
            )

        merchant = Merchant(
            id=DEMO_MERCHANT_ID,
            name=DEMO_NAME,
            email=DEMO_EMAIL,
            password_hash=hash_password(
                DEMO_PASSWORD,
            ),
        )

        await merchant_repository.insert(
            merchant,
        )

        logger.info(
            "Created canonical demo merchant: %s (%s)",
            DEMO_EMAIL,
            DEMO_MERCHANT_ID,
        )

    # --------------------------------------------------------
    # 2. Ensure the canonical demo customer exists.
    # --------------------------------------------------------

    customer_repository = get_customer_repository()

    customer = await customer_repository.find_by_id(
        DEMO_CUSTOMER_ID,
    )

    if customer is None:
        customer = Customer(
            id=DEMO_CUSTOMER_ID,
            merchant_id=DEMO_MERCHANT_ID,
            name="Demo Customer (Seed Data)",
            email="demo.customer@recoverai.com",
            phone="+91 90000 00000",
            risk_score=0.42,
        )

        await customer_repository.insert(
            customer,
        )

        logger.info(
            "Created demo customer: %s",
            DEMO_CUSTOMER_ID,
        )
    else:
        logger.info(
            "Demo customer already exists: %s",
            DEMO_CUSTOMER_ID,
        )

    # --------------------------------------------------------
    # 3. Ensure the canonical demo payment exists.
    # --------------------------------------------------------

    payment_repository = get_payment_repository()

    payment = await payment_repository.find_by_id(
        DEMO_PAYMENT_ID,
    )

    if payment is None:
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

        await payment_repository.insert(
            payment,
        )

        logger.info(
            "Created demo payment: %s",
            DEMO_PAYMENT_ID,
        )
    else:
        logger.info(
            "Demo payment already exists: %s",
            DEMO_PAYMENT_ID,
        )

    # --------------------------------------------------------
    # 4. Ensure the canonical payment attempt exists.
    # --------------------------------------------------------

    payment_attempt_repository = get_payment_attempt_repository()

    payment_attempt = await payment_attempt_repository.find_by_id(
        DEMO_PAYMENT_ATTEMPT_ID,
    )

    if payment_attempt is None:
        payment_attempt = PaymentAttempt(
            id=DEMO_PAYMENT_ATTEMPT_ID,
            payment_id=DEMO_PAYMENT_ID,
            attempt_number=1,
            status=PaymentAttemptStatus.FAILED,
            failure_reason="Insufficient Funds",
        )

        await payment_attempt_repository.insert(
            payment_attempt,
        )

        logger.info(
            "Created demo payment attempt: %s",
            DEMO_PAYMENT_ATTEMPT_ID,
        )
    else:
        logger.info(
            "Demo payment attempt already exists: %s",
            DEMO_PAYMENT_ATTEMPT_ID,
        )

    # --------------------------------------------------------
    # 5. Ensure the canonical recovery case exists.
    # --------------------------------------------------------

    recovery_case_repository = get_recovery_case_repository()

    recovery_case = await recovery_case_repository.find_by_id(
        DEMO_RECOVERY_CASE_ID,
    )

    if recovery_case is None:
        recovery_case = RecoveryCase(
            id=DEMO_RECOVERY_CASE_ID,
            payment_id=DEMO_PAYMENT_ID,
            customer_id=DEMO_CUSTOMER_ID,
            recovery_probability=0.5,
            status=RecoveryCaseStatus.PENDING,
            recommended_action=RecommendedAction.SMART_RETRY,
        )

        await recovery_case_repository.insert(
            recovery_case,
        )

        logger.info(
            "Created demo recovery case: %s",
            DEMO_RECOVERY_CASE_ID,
        )
    else:
        logger.info(
            "Demo recovery case already exists: %s",
            DEMO_RECOVERY_CASE_ID,
        )

    # --------------------------------------------------------
    # 6. Ensure the canonical audit log exists.
    # --------------------------------------------------------

    audit_log_repository = get_audit_log_repository()

    audit_log = await audit_log_repository.find_by_id(
        DEMO_AUDIT_LOG_ID,
    )

    if audit_log is None:
        audit_log = AuditLog(
            id=DEMO_AUDIT_LOG_ID,
            payment_id=DEMO_PAYMENT_ID,
            action=RecommendedAction.SMART_RETRY.value,
            reason=(
                "Seed data placeholder — "
                "not a real automated decision."
            ),
            confidence=0.5,
        )

        await audit_log_repository.insert(
            audit_log,
        )

        logger.info(
            "Created demo audit log: %s",
            DEMO_AUDIT_LOG_ID,
        )
    else:
        logger.info(
            "Demo audit log already exists: %s",
            DEMO_AUDIT_LOG_ID,
        )

    logger.info(
        "Canonical RecoverAI demo environment ready "
        "for merchant %s.",
        DEMO_MERCHANT_ID,
    )