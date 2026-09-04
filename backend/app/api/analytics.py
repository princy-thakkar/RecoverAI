from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter

from app.models.domain import (
    PaymentAttemptStatus,
    PaymentStatus,
)
from app.repositories.entities import (
    get_payment_attempt_repository,
    get_payment_repository,
    get_recovery_case_repository,
)
from app.schemas.api import AnalyticsDTO


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get(
    "",
    response_model=AnalyticsDTO,
    response_model_by_alias=True,
)
async def get_analytics():
    payments = await get_payment_repository().find_many(
        limit=1000
    )

    attempts = await get_payment_attempt_repository().find_many(
        limit=1000
    )

    # Keep this query because recovery cases are part of the
    # analytics domain and may be used for future metrics
    # without changing the public contract.
    await get_recovery_case_repository().find_many(
        limit=1000
    )

    payment_map = {
        str(payment.id): payment
        for payment in payments
    }

    recovered_statuses = {
        PaymentStatus.RECOVERED,
        PaymentStatus.SUCCESSFUL,
    }

    at_risk_statuses = {
        PaymentStatus.FAILED,
        PaymentStatus.AT_RISK,
        PaymentStatus.RECOVERING,
    }

    recovered_payments = [
        payment
        for payment in payments
        if payment.status in recovered_statuses
    ]

    at_risk_payments = [
        payment
        for payment in payments
        if payment.status in at_risk_statuses
    ]

    revenue_at_risk = sum(
        payment.amount
        for payment in at_risk_payments
    )

    revenue_recovered = sum(
        payment.amount
        for payment in recovered_payments
    )

    recovery_attempts = len(attempts)

    successful_recoveries = sum(
        1
        for attempt in attempts
        if attempt.status
        == PaymentAttemptStatus.SUCCESS
    )

    recovery_rate = (
        successful_recoveries
        / recovery_attempts
        * 100
        if recovery_attempts
        else 0
    )

    method_data: dict[
        str,
        dict[str, float],
    ] = defaultdict(
        lambda: {
            "recovered": 0.0,
            "attempted": 0.0,
        }
    )

    for attempt in attempts:
        payment = payment_map.get(
            str(attempt.payment_id)
        )

        if not payment:
            continue

        method = payment.payment_method

        method_data[method]["attempted"] += (
            payment.amount
        )

        if attempt.status == PaymentAttemptStatus.SUCCESS:
            method_data[method]["recovered"] += (
                payment.amount
            )

    reason_data: dict[
        str,
        dict[str, float],
    ] = defaultdict(
        lambda: {
            "recovered": 0.0,
            "attempted": 0.0,
        }
    )

    for payment in payments:
        if not payment.failure_reason:
            continue

        reason = payment.failure_reason

        reason_data[reason]["attempted"] += (
            payment.amount
        )

        if payment.status in recovered_statuses:
            reason_data[reason]["recovered"] += (
                payment.amount
            )

    performance: dict[
        str,
        dict[str, float],
    ] = defaultdict(
        lambda: {
            "recovered": 0.0,
            "atRisk": 0.0,
        }
    )

    for payment in payments:
        label = (
            payment.created_at.strftime("%b %d")
            if payment.created_at
            else "Current"
        )

        if payment.status in recovered_statuses:
            performance[label]["recovered"] += (
                payment.amount
            )

        elif payment.status in at_risk_statuses:
            performance[label]["atRisk"] += (
                payment.amount
            )

    performance_over_time = [
        {
            "label": label,
            **values,
        }
        for label, values in performance.items()
    ] or [
        {
            "label": "Current",
            "recovered": revenue_recovered,
            "atRisk": revenue_at_risk,
        }
    ]

    return {
        "revenueAtRisk": revenue_at_risk,
        "revenueRecovered": revenue_recovered,
        "recoveryRate": round(
            recovery_rate,
            2,
        ),
        "recoveryAttempts": recovery_attempts,
        "successfulRecoveries": successful_recoveries,
        "recoveryByMethod": [
            {
                "method": method,
                **values,
            }
            for method, values in method_data.items()
        ],
        "recoveryByReason": [
            {
                "reason": reason,
                **values,
            }
            for reason, values in reason_data.items()
        ],
        "performanceOverTime": performance_over_time,
    }