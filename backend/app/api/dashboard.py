from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.models.domain import PaymentAttemptStatus, PaymentStatus
from app.repositories.entities import (
    get_customer_repository,
    get_payment_attempt_repository,
    get_payment_repository,
    get_recovery_case_repository,
)
from app.schemas.api import DashboardDTO


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


def _status(value) -> str:
    """
    Normalize enum/string status values to their string representation.
    """
    return getattr(value, "value", value)


def _to_datetime(value) -> datetime | None:
    """
    Convert supported datetime/string values into timezone-aware UTC datetimes.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        result = value
    else:
        try:
            result = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        except (TypeError, ValueError):
            return None

    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)

    return result.astimezone(timezone.utc)


def _payment_datetime(payment) -> datetime | None:
    """
    Use the payment creation timestamp when available.

    The fallback chain makes the dashboard resilient if an older
    payment record does not contain created_at.
    """
    for field in ("created_at", "updated_at"):
        value = getattr(payment, field, None)
        parsed = _to_datetime(value)

        if parsed is not None:
            return parsed

    return None


def _attempt_datetime(attempt) -> datetime | None:
    return _to_datetime(
        getattr(attempt, "attempted_at", None)
    )


def _build_revenue_chart(payments, attempts):
    """
    Build a real seven-point revenue trend from database data.

    Recovered revenue is attributed to the successful recovery attempt
    date when available.

    At-risk revenue is attributed to the payment date.

    No values are hardcoded.
    """
    payment_dates = [
        date
        for payment in payments
        if (date := _payment_datetime(payment)) is not None
    ]

    attempt_dates = [
        date
        for attempt in attempts
        if (date := _attempt_datetime(attempt)) is not None
    ]

    all_dates = payment_dates + attempt_dates

    if all_dates:
        latest_date = max(all_dates).date()
    else:
        latest_date = datetime.now(timezone.utc).date()

    start_date = latest_date - timedelta(days=6)

    days = [
        start_date + timedelta(days=index)
        for index in range(7)
    ]

    chart = {
        day: {
            "label": day.strftime("%b %d"),
            "recovered": 0.0,
            "atRisk": 0.0,
        }
        for day in days
    }

    at_risk_statuses = {
        _status(PaymentStatus.FAILED),
        _status(PaymentStatus.AT_RISK),
        _status(PaymentStatus.RECOVERING),
    }

    # Current revenue at risk, grouped by payment date.
    for payment in payments:
        if _status(payment.status) not in at_risk_statuses:
            continue

        payment_date = _payment_datetime(payment)

        if payment_date is None:
            continue

        day = payment_date.date()

        if day not in chart:
            continue

        chart[day]["atRisk"] += float(payment.amount)

    # Recovered revenue is grouped by the successful recovery
    # attempt date rather than the original payment creation date.
    successful_attempts = {}

    for attempt in attempts:
        if _status(attempt.status) != _status(
            PaymentAttemptStatus.SUCCESS
        ):
            continue

        attempt_date = _attempt_datetime(attempt)

        if attempt_date is None:
            continue

        payment_id = str(attempt.payment_id)

        previous = successful_attempts.get(payment_id)

        if previous is None or attempt_date > previous:
            successful_attempts[payment_id] = attempt_date

    recovered_status = _status(PaymentStatus.RECOVERED)

    for payment in payments:
        if _status(payment.status) != recovered_status:
            continue

        recovery_date = successful_attempts.get(
            str(payment.id)
        )

        if recovery_date is None:
            recovery_date = _payment_datetime(payment)

        if recovery_date is None:
            continue

        day = recovery_date.date()

        if day not in chart:
            continue

        chart[day]["recovered"] += float(payment.amount)

    return [
        {
            "label": chart[day]["label"],
            "recovered": round(
                chart[day]["recovered"],
                2,
            ),
            "atRisk": round(
                chart[day]["atRisk"],
                2,
            ),
        }
        for day in days
    ]


@router.get(
    "/stats",
    response_model=DashboardDTO,
    response_model_by_alias=True,
)
async def get_dashboard_stats():
    payment_repository = get_payment_repository()
    attempt_repository = get_payment_attempt_repository()
    recovery_repository = get_recovery_case_repository()
    customer_repository = get_customer_repository()

    payments = await payment_repository.find_many(
        limit=1000
    )

    attempts = await attempt_repository.find_many(
        limit=1000
    )

    recovery_cases = await recovery_repository.find_many(
        limit=1000
    )

    customers = await customer_repository.find_many(
        limit=1000
    )

    customer_map = {
        str(customer.id): customer
        for customer in customers
    }

    payment_map = {
        str(payment.id): payment
        for payment in payments
    }

    successful_payment_statuses = {
        _status(PaymentStatus.SUCCESSFUL),
        _status(PaymentStatus.RECOVERED),
    }

    successful_payments = [
        payment
        for payment in payments
        if _status(payment.status)
        in successful_payment_statuses
    ]

    failed_payments = [
        payment
        for payment in payments
        if _status(payment.status)
        == _status(PaymentStatus.FAILED)
    ]

    recovered_payments = [
        payment
        for payment in payments
        if _status(payment.status)
        == _status(PaymentStatus.RECOVERED)
    ]

    at_risk_statuses = {
        _status(PaymentStatus.FAILED),
        _status(PaymentStatus.AT_RISK),
        _status(PaymentStatus.RECOVERING),
    }

    revenue_at_risk = sum(
        payment.amount
        for payment in payments
        if _status(payment.status)
        in at_risk_statuses
    )

    revenue_recovered = sum(
        payment.amount
        for payment in recovered_payments
    )

    successful_attempts = sum(
        1
        for attempt in attempts
        if _status(attempt.status)
        == _status(PaymentAttemptStatus.SUCCESS)
    )

    recovery_rate = (
        successful_attempts / len(attempts) * 100
        if attempts
        else 0
    )

    status_chart = [
        {
            "label": "All",
            "successful": len(successful_payments),
            "failed": len(failed_payments),
        }
    ]

    # Real seven-day revenue trend.
    revenue_chart = _build_revenue_chart(
        payments,
        attempts,
    )

    recent_attempts = []

    sorted_attempts = sorted(
        attempts,
        key=lambda item: (
            _attempt_datetime(item)
            or datetime.min.replace(tzinfo=timezone.utc)
        ),
        reverse=True,
    )

    for attempt in sorted_attempts[:10]:
        payment = payment_map.get(
            str(attempt.payment_id)
        )

        customer = (
            customer_map.get(str(payment.customer_id))
            if payment
            else None
        )

        attempt_status = _status(attempt.status)

        recent_attempts.append(
            {
                "id": attempt.id,
                "customerName": (
                    customer.name
                    if customer
                    else "Unknown Customer"
                ),
                "amount": (
                    payment.amount
                    if payment
                    else 0
                ),
                "action": "SMART_RETRY",
                "status": (
                    "recovered"
                    if attempt_status
                    == _status(PaymentAttemptStatus.SUCCESS)
                    else attempt_status
                ),
                "timestamp": (
                    attempt.attempted_at.isoformat()
                ),
            }
        )

    failure_reason_map: dict[
        str,
        dict[str, float | int | str],
    ] = {}

    for payment in payments:
        if not payment.failure_reason:
            continue

        reason = payment.failure_reason

        entry = failure_reason_map.setdefault(
            reason,
            {
                "reason": reason,
                "count": 0,
                "amount": 0,
            },
        )

        entry["count"] = (
            int(entry["count"]) + 1
        )

        entry["amount"] = (
            float(entry["amount"])
            + payment.amount
        )

    top_failure_reasons = sorted(
        failure_reason_map.values(),
        key=lambda item: int(item["count"]),
        reverse=True,
    )[:5]

    recommendations = []

    for case in recovery_cases:
        payment = payment_map.get(
            str(case.payment_id)
        )

        if (
            not payment
            or _status(payment.status)
            not in at_risk_statuses
        ):
            continue

        if case.recovery_probability < 0.70:
            continue

        customer = customer_map.get(
            str(payment.customer_id)
        )

        recommendations.append(
            {
                "id": case.id,
                "paymentId": payment.id,
                "customerName": (
                    customer.name
                    if customer
                    else "Unknown Customer"
                ),
                "amount": payment.amount,
                "reason": (
                    payment.failure_reason
                    or "Unknown"
                ),
                "probability": round(
                    case.recovery_probability * 100,
                    2,
                ),
                "action": case.recommended_action,
                "rationale": (
                    "This payment has a high predicted "
                    "recovery probability. A recovery "
                    "attempt is recommended."
                ),
            }
        )

    recommendations.sort(
        key=lambda item: (
            item["probability"],
            item["amount"],
        ),
        reverse=True,
    )

    return {
        "stats": {
            "totalTransactions": len(payments),
            "successfulPayments": len(
                successful_payments
            ),
            "failedPayments": len(
                failed_payments
            ),
            "revenueAtRisk": revenue_at_risk,
            "revenueRecovered": revenue_recovered,
            "recoveryRate": round(
                recovery_rate,
                2,
            ),
        },
        "revenueChart": revenue_chart,
        "statusChart": status_chart,
        "recentAttempts": recent_attempts,
        "topFailureReasons": top_failure_reasons,
        "recommendations": recommendations,
    }