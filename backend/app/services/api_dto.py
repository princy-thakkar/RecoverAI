"""Mapping from internal domain models to public RecoverAI API DTOs."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.ai.reasoning import analyze_recovery_decision
from app.ml.decision import choose_recovery_action
from app.ml.predict import predict_recovery_probability
from app.models.domain import (
    AuditLog,
    Customer,
    Payment,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
    RecommendedAction,
    RecoveryCase,
)
from app.schemas.api import (
    AIAnalysisDTO,
    CustomerDTO,
    PaymentAttemptDTO,
    PaymentDTO,
    RecoveryCaseDTO,
    TimelineEventDTO,
)


def _status_value(status: Any) -> str:
    """Return the public string value for an enum or already-serialized string."""
    return getattr(status, "value", status)


def _iso(value: Any) -> str | None:
    """Convert a datetime-like value to an ISO-8601 string."""
    return value.isoformat() if value else None


def _attempt_dto(attempt: PaymentAttempt, payment: Payment) -> PaymentAttemptDTO:
    return PaymentAttemptDTO(
        id=attempt.id,
        paymentId=attempt.payment_id,
        attemptNumber=attempt.attempt_number,
        method=payment.payment_method,
        amount=payment.amount,
        status=attempt.status,
        failureReason=attempt.failure_reason,
        timestamp=_iso(attempt.attempted_at),
    )


def _timeline(
    payment: Payment,
    attempts: list[PaymentAttempt],
    recovery_case: RecoveryCase | None,
) -> list[TimelineEventDTO]:
    events: list[TimelineEventDTO] = [
        TimelineEventDTO(
            id=f"{payment.id}:created",
            type="Payment Created",
            title="Payment Created",
            description="Transaction initiated by customer.",
            timestamp=_iso(payment.created_at),
            status="completed",
        )
    ]

    if payment.failure_reason:
        events.append(
            TimelineEventDTO(
                id=f"{payment.id}:failed",
                type="Payment Failed",
                title="Payment Failed",
                description=f"Payment failed: {payment.failure_reason}.",
                timestamp=_iso(payment.created_at),
                status="completed",
            )
        )

    if recovery_case:
        recommended_action = _status_value(recovery_case.recommended_action)
        recovery_status = _status_value(recovery_case.status)

        events.append(
            TimelineEventDTO(
                id=f"{recovery_case.id}:decision",
                type="Recovery Action Selected",
                title="Recovery Action Selected",
                description=(
                    f"RecoverAI recommends {recommended_action}."
                ),
                timestamp=_iso(recovery_case.updated_at),
                status=(
                    "completed"
                    if recovery_status in {"recovered", "failed"}
                    else "current"
                ),
            )
        )

    for attempt in sorted(attempts, key=lambda item: item.attempt_number):
        succeeded = _status_value(attempt.status) == PaymentAttemptStatus.SUCCESS.value

        events.append(
            TimelineEventDTO(
                id=f"{payment.id}:attempt:{attempt.attempt_number}",
                type="Recovery Attempt",
                title=f"Recovery Attempt #{attempt.attempt_number}",
                description=(
                    "Recovery attempt succeeded."
                    if succeeded
                    else (
                        f"Recovery attempt failed: {attempt.failure_reason}."
                        if attempt.failure_reason
                        else "Recovery attempt failed."
                    )
                ),
                timestamp=_iso(attempt.attempted_at),
                status="completed",
            )
        )

    if _status_value(payment.status) == PaymentStatus.RECOVERED.value:
        events.append(
            TimelineEventDTO(
                id=f"{payment.id}:recovered",
                type="Payment Recovered",
                title="Payment Recovered",
                description="Payment was successfully recovered.",
                timestamp=_iso(
                    attempts[-1].attempted_at
                    if attempts
                    else payment.created_at
                ),
                status="completed",
            )
        )
    elif (
        recovery_case
        and _status_value(recovery_case.status)
        not in {"recovered", "failed"}
    ):
        events.append(
            TimelineEventDTO(
                id=f"{payment.id}:pending",
                type="Recovery Pending",
                title="Recovery Pending",
                description="The recommended recovery action is awaiting completion.",
                timestamp=None,
                status="pending",
            )
        )

    return events


def _prediction(
    payment: Payment,
    attempts: list[PaymentAttempt],
    recovery_case: RecoveryCase | None,
) -> tuple[float, Any, AIAnalysisDTO]:
    previous_attempts = len(attempts)
    failed_attempts = sum(
        1
        for attempt in attempts
        if _status_value(attempt.status) == PaymentAttemptStatus.FAILED.value
    )

    payment_data = payment.model_dump()
    payment_data["previous_attempts"] = previous_attempts
    payment_data["failed_attempts"] = failed_attempts

    if _status_value(payment.status) in {
        PaymentStatus.SUCCESSFUL.value,
        PaymentStatus.RECOVERED.value,
    }:
        probability = 1.0
        action = RecommendedAction.STOP
    elif recovery_case is not None:
        probability = recovery_case.recovery_probability

        raw_action = recovery_case.recommended_action
        action = (
            raw_action
            if isinstance(raw_action, RecommendedAction)
            else RecommendedAction(raw_action)
        )
    else:
        probability = predict_recovery_probability(payment_data)
        action = choose_recovery_action(
            probability=probability,
            failure_reason=payment.failure_reason,
            attempts=previous_attempts,
        )

    explanation = analyze_recovery_decision(
        payment=payment_data,
        probability=probability,
        recommended_action=_status_value(action),
    )

    return probability, action, AIAnalysisDTO.model_validate(explanation)


async def build_payment_dto(
    payment: Payment,
    customer: Customer | None,
    attempts: list[PaymentAttempt],
    recovery_case: RecoveryCase | None,
) -> PaymentDTO:
    probability, action, explanation = _prediction(
        payment,
        attempts,
        recovery_case,
    )

    return PaymentDTO(
        id=payment.id,
        customerId=payment.customer_id,
        customerName=customer.name if customer else "Unknown Customer",
        customerEmail=str(customer.email) if customer else "",
        amount=payment.amount,
        currency=payment.currency,
        paymentMethod=payment.payment_method,
        status=payment.status,
        failureReason=payment.failure_reason,
        recoveryProbability=round(probability * 100, 2),
        lastAttempt=_iso(attempts[-1].attempted_at) if attempts else None,
        recommendedAction=action,
        createdAt=_iso(payment.created_at),
        attempts=[_attempt_dto(attempt, payment) for attempt in attempts],
        timeline=_timeline(payment, attempts, recovery_case),
        aiExplanation=explanation,
    )


def build_customer_dto(
    customer: Customer,
    payments: Iterable[Payment],
    recovery_cases: Iterable[RecoveryCase],
) -> CustomerDTO:
    customer_payments = [p for p in payments if p.customer_id == customer.id]
    cases = [c for c in recovery_cases if c.customer_id == customer.id]

    successful = sum(
        1
        for payment in customer_payments
        if _status_value(payment.status)
        in {
            PaymentStatus.SUCCESSFUL.value,
            PaymentStatus.RECOVERED.value,
        }
    )

    failed = sum(
        1
        for payment in customer_payments
        if _status_value(payment.status)
        in {
            PaymentStatus.FAILED.value,
            PaymentStatus.AT_RISK.value,
            PaymentStatus.RECOVERING.value,
        }
    )

    probability = (
        sum(case.recovery_probability for case in cases)
        / len(cases)
        * 100
        if cases
        else 0.0
    )

    risk_score = customer.risk_score

    if risk_score < 0.34:
        risk_profile = "Low Risk"
    elif risk_score < 0.67:
        risk_profile = "Medium Risk"
    else:
        risk_profile = "High Risk"

    return CustomerDTO(
        id=customer.id,
        name=customer.name,
        email=str(customer.email),
        phone=customer.phone,
        totalPayments=len(customer_payments),
        successfulPayments=successful,
        failedPayments=failed,
        totalAmount=sum(p.amount for p in customer_payments),
        recoveryProbability=round(probability, 2),
        riskProfile=risk_profile,
        joinedAt=_iso(customer.created_at),
    )


def build_recovery_case_dto(
    case: RecoveryCase,
    payment: Payment | None,
    customer: Customer | None,
    attempt_count: int,
) -> RecoveryCaseDTO:
    payment_data = (
        payment.model_dump()
        if payment
        else {
            "amount": 0,
            "payment_method": "Unknown",
            "failure_reason": "Unknown",
        }
    )

    payment_data["previous_attempts"] = attempt_count
    payment_data["failed_attempts"] = attempt_count

    recommended_action = _status_value(case.recommended_action)

    explanation = analyze_recovery_decision(
        payment=payment_data,
        probability=case.recovery_probability,
        recommended_action=recommended_action,
    )

    return RecoveryCaseDTO(
        id=case.id,
        paymentId=case.payment_id,
        customerId=case.customer_id,
        customerName=customer.name if customer else "Unknown Customer",
        amountAtRisk=payment.amount if payment else 0,
        failureReason=(
            payment.failure_reason
            if payment and payment.failure_reason
            else "Unknown"
        ),
        recoveryProbability=round(case.recovery_probability * 100, 2),
        recommendedAction=case.recommended_action,
        status=case.status,
        attempts=attempt_count,
        createdAt=_iso(case.created_at),
        lastUpdated=_iso(case.updated_at),
        aiExplanation=AIAnalysisDTO.model_validate(explanation),
    )
