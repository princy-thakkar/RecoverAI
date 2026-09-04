"""Public payment-attempt API using frontend-facing DTOs."""
from fastapi import APIRouter

from app.api.auth import CurrentMerchant
from app.repositories.entities import (
    get_payment_attempt_repository,
    get_payment_repository,
)
from app.schemas.api import PaymentAttemptDTO
from app.services.api_dto import _attempt_dto


router = APIRouter(
    prefix="/payment-attempts",
    tags=["payment-attempts"],
)


@router.get(
    "",
    response_model=list[PaymentAttemptDTO],
    response_model_by_alias=True,
)
async def list_payment_attempts(merchant: CurrentMerchant):
    """Return payment attempts belonging only to the current merchant."""

    merchant_id = str(merchant.id)

    payments = await get_payment_repository().find_many(
        {"merchant_id": merchant_id},
        limit=1000,
    )

    payment_map = {
        str(payment.id): payment
        for payment in payments
    }

    payment_ids = list(payment_map)

    attempts = await get_payment_attempt_repository().find_many(
        {"payment_id": {"$in": payment_ids}},
        limit=100,
    )

    return [
        _attempt_dto(
            attempt,
            payment_map[str(attempt.payment_id)],
        )
        for attempt in attempts
        if str(attempt.payment_id) in payment_map
    ]
