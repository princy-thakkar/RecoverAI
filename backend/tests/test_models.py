"""
Model validation tests — no database required.

These confirm the Pydantic domain models accept valid data, apply their
defaults correctly, and reject invalid data per their declared constraints.
"""
import pytest
from pydantic import ValidationError

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


def test_merchant_generates_id_and_created_at_by_default():
    merchant = Merchant(name="Acme Retail", email="billing@acme.com")
    assert merchant.id
    assert merchant.created_at is not None


def test_merchant_rejects_invalid_email():
    with pytest.raises(ValidationError):
        Merchant(name="Acme Retail", email="not-an-email")


def test_customer_requires_merchant_id_and_valid_risk_score():
    customer = Customer(
        merchant_id="MERCHANT_1",
        name="Jane Doe",
        email="jane@example.com",
        phone="+91 90000 00000",
        risk_score=0.35,
    )
    assert customer.merchant_id == "MERCHANT_1"
    assert 0 <= customer.risk_score <= 1


def test_customer_rejects_risk_score_out_of_range():
    with pytest.raises(ValidationError):
        Customer(
            merchant_id="MERCHANT_1",
            name="Jane Doe",
            email="jane@example.com",
            phone="+91 90000 00000",
            risk_score=1.5,
        )


def test_payment_defaults_currency_to_inr_and_requires_positive_amount():
    payment = Payment(
        merchant_id="MERCHANT_1",
        customer_id="CUSTOMER_1",
        amount=999.0,
        status=PaymentStatus.FAILED,
        payment_method="UPI",
        failure_reason="Insufficient Funds",
    )
    assert payment.currency == "INR"

    with pytest.raises(ValidationError):
        Payment(
            merchant_id="MERCHANT_1",
            customer_id="CUSTOMER_1",
            amount=0,
            status=PaymentStatus.FAILED,
            payment_method="UPI",
        )


def test_payment_attempt_requires_attempt_number_at_least_one():
    attempt = PaymentAttempt(
        payment_id="PAYMENT_1",
        attempt_number=1,
        status=PaymentAttemptStatus.FAILED,
    )
    assert attempt.attempt_number == 1

    with pytest.raises(ValidationError):
        PaymentAttempt(
            payment_id="PAYMENT_1",
            attempt_number=0,
            status=PaymentAttemptStatus.FAILED,
        )


def test_recovery_case_accepts_valid_probability_and_action():
    case = RecoveryCase(
        payment_id="PAYMENT_1",
        customer_id="CUSTOMER_1",
        recovery_probability=0.82,
        status=RecoveryCaseStatus.PENDING,
        recommended_action=RecommendedAction.SMART_RETRY,
    )
    assert case.recovery_probability == 0.82
    assert case.recommended_action == RecommendedAction.SMART_RETRY


def test_recovery_case_rejects_probability_above_one():
    with pytest.raises(ValidationError):
        RecoveryCase(
            payment_id="PAYMENT_1",
            customer_id="CUSTOMER_1",
            recovery_probability=1.2,
            status=RecoveryCaseStatus.PENDING,
            recommended_action=RecommendedAction.SMART_RETRY,
        )


def test_audit_log_requires_confidence_between_zero_and_one():
    log = AuditLog(
        payment_id="PAYMENT_1",
        action=RecommendedAction.SMART_RETRY.value,
        reason="High recovery probability and failure appears temporary.",
        confidence=0.82,
    )
    assert log.confidence == 0.82

    with pytest.raises(ValidationError):
        AuditLog(
            payment_id="PAYMENT_1",
            action=RecommendedAction.SMART_RETRY.value,
            reason="Invalid confidence test",
            confidence=-0.1,
        )