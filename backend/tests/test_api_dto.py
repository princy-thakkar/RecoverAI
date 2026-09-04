from datetime import datetime, timezone

from app.models.domain import (
    Customer,
    Payment,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
    RecommendedAction,
    RecoveryCase,
    RecoveryCaseStatus,
)
from app.services.api_dto import (
    build_customer_dto,
    build_payment_dto,
    build_recovery_case_dto,
)


def make_payment():
    now = datetime.now(timezone.utc)

    return Payment(
        id="DEMO_PAYMENT_1",
        merchant_id="DEMO_MERCHANT_1",
        customer_id="DEMO_CUSTOMER_1",
        amount=1499,
        currency="INR",
        status=PaymentStatus.FAILED,
        payment_method="UPI",
        failure_reason="Insufficient Funds",
        created_at=now,
    )


def make_customer():
    return Customer(
        id="DEMO_CUSTOMER_1",
        merchant_id="DEMO_MERCHANT_1",
        name="Demo Customer",
        email="demo@example.com",
        phone="+91 90000 00000",
        risk_score=0.42,
    )


def make_attempt():
    return PaymentAttempt(
        id="ATTEMPT_1",
        payment_id="DEMO_PAYMENT_1",
        attempt_number=1,
        status=PaymentAttemptStatus.FAILED,
        failure_reason="Insufficient Funds",
    )


def test_payment_dto_uses_camel_case_and_enrichment(
    monkeypatch,
):
    payment = make_payment()
    customer = make_customer()
    attempt = make_attempt()

    monkeypatch.setattr(
        "app.services.api_dto.predict_recovery_probability",
        lambda _: 0.91,
    )

    dto = __import__("asyncio").run(
        build_payment_dto(
            payment,
            customer,
            [attempt],
            None,
        )
    )

    payload = dto.model_dump(
        by_alias=True
    )

    assert (
        payload["customerName"]
        == "Demo Customer"
    )

    assert (
        payload["paymentMethod"]
        == "UPI"
    )

    assert (
        payload["recoveryProbability"]
        == 91.0
    )

    assert (
        payload["attempts"][0][
            "paymentId"
        ]
        == "DEMO_PAYMENT_1"
    )

    assert (
        payload["attempts"][0]["amount"]
        == 1499
    )

    assert payload["timeline"]

    assert (
        payload["aiExplanation"][
            "recommendedAction"
        ]
        == "SMART_RETRY"
    )

    assert "customer_id" not in payload


def test_customer_dto_aggregates_payment_metrics():
    customer = make_customer()
    payment = make_payment()

    dto = build_customer_dto(
        customer,
        [payment],
        [],
    )

    payload = dto.model_dump(
        by_alias=True
    )

    assert payload["totalPayments"] == 1
    assert payload["failedPayments"] == 1
    assert payload["successfulPayments"] == 0
    assert payload["totalAmount"] == 1499
    assert (
        payload["riskProfile"]
        == "Medium Risk"
    )


def test_recovery_case_dto_uses_public_probability_and_explanation():
    payment = make_payment()
    customer = make_customer()

    case = RecoveryCase(
        id="CASE_1",
        payment_id=payment.id,
        customer_id=customer.id,
        recovery_probability=0.91,
        status=RecoveryCaseStatus.PENDING,
        recommended_action=(
            RecommendedAction.SMART_RETRY
        ),
    )

    dto = build_recovery_case_dto(
        case,
        payment,
        customer,
        1,
    )

    payload = dto.model_dump(
        by_alias=True
    )

    assert (
        payload["paymentId"]
        == payment.id
    )

    assert (
        payload["recoveryProbability"]
        == 91.0
    )

    assert (
        payload["recommendedAction"]
        == "SMART_RETRY"
    )

    assert (
        payload["aiExplanation"][
            "probabilityPercent"
        ]
        == 91.0
    )