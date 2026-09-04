"""Public payment API using frontend-facing DTOs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import CurrentMerchant
from app.models.domain import (
    Payment,
    PaymentStatus,
    RecoveryCase,
    RecoveryCaseStatus,
    RecommendedAction,
)
from app.agent.decision import choose_recovery_action
from app.ml.predict import predict_recovery_probability
from app.repositories.entities import (
    get_customer_repository,
    get_payment_attempt_repository,
    get_payment_repository,
    get_recovery_case_repository,
)
from app.schemas.api import PaymentDTO
from app.services.api_dto import build_payment_dto


router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


class CreatePaymentRequest(BaseModel):
    customerId: str
    amount: float = Field(gt=0)
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )
    status: PaymentStatus
    paymentMethod: str = Field(min_length=1)
    failureReason: str | None = None


async def _build_payment(
    payment: Payment,
) -> PaymentDTO:
    customer = await get_customer_repository().find_one(
        {
            "id": payment.customer_id,
            "merchant_id": payment.merchant_id,
        }
    )

    attempts = await get_payment_attempt_repository().find_many(
        {
            "payment_id": payment.id,
        },
        limit=100,
    )

    recovery_case = await get_recovery_case_repository().find_one(
        {
            "payment_id": payment.id,
            "merchant_id": payment.merchant_id,
        }
    )

    return await build_payment_dto(
        payment,
        customer,
        attempts,
        recovery_case,
    )

@router.get(
    "",
    response_model=list[PaymentDTO],
    response_model_by_alias=True,
)
async def list_payments(current_merchant: CurrentMerchant):
    repository = get_payment_repository()

    payments = await repository.find_many(
        {"merchant_id": current_merchant.id},
        limit=100,
    )

    return [
        await _build_payment(payment)
        for payment in payments
    ]


@router.get(
    "/{payment_id}",
    response_model=PaymentDTO,
    response_model_by_alias=True,
)
async def get_payment(
    payment_id: str,
    current_merchant: CurrentMerchant,
):
    payments = await get_payment_repository().find_many(
        {
            "id": payment_id,
            "merchant_id": str(current_merchant.id),
        },
        limit=1,
    )

    payment = payments[0] if payments else None

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return await _build_payment(payment)

@router.post(
    "",
    response_model=PaymentDTO,
    response_model_by_alias=True,
)
async def create_payment(
    request: CreatePaymentRequest,
    current_merchant: CurrentMerchant,
):
    customer = await get_customer_repository().find_one(
        {
            "id": request.customerId,
            "merchant_id": current_merchant.id,
        }
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found for this merchant",
        )

    payment = Payment(
        merchant_id=current_merchant.id,
        customer_id=request.customerId,
        amount=request.amount,
        currency=request.currency.upper(),
        status=request.status,
        payment_method=request.paymentMethod,
        failure_reason=request.failureReason,
    )

    await get_payment_repository().insert(payment)

    if payment.status in (
        PaymentStatus.FAILED,
        PaymentStatus.AT_RISK,
    ):
        payment_data = payment.model_dump()

        probability = predict_recovery_probability(
            payment_data
        )

        action = choose_recovery_action(
            probability=probability,
            failure_reason=payment.failure_reason,
            attempts=0,
        )

        recovery_case = RecoveryCase(
            payment_id=payment.id,
            customer_id=payment.customer_id,
            recovery_probability=probability,
            status=(
                RecoveryCaseStatus.AWAITING_CUSTOMER
                if action in (
                    RecommendedAction.REMINDER,
                    RecommendedAction.PAYMENT_METHOD_SUGGESTION,
                )
                else RecoveryCaseStatus.IN_PROGRESS
                if action == RecommendedAction.SUPPORT_ESCALATION
                else RecoveryCaseStatus.RETRY_SCHEDULED
            ),
            recommended_action=action,
        )

        await get_recovery_case_repository().insert(
            recovery_case
        )

    return await _build_payment(payment)