"""Public customer API using frontend-facing DTOs."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import CurrentMerchant
from app.models.domain import Customer
from app.repositories.entities import (
    get_customer_repository,
    get_payment_repository,
    get_recovery_case_repository,
)
from app.schemas.api import CustomerDTO
from app.services.api_dto import build_customer_dto


router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


class CreateCustomerRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    phone: str | None = None
    riskScore: float = Field(default=0.5, ge=0, le=1)


@router.post(
    "",
    response_model=CustomerDTO,
    response_model_by_alias=True,
)
async def create_customer(
    request: CreateCustomerRequest,
    current_merchant: CurrentMerchant,
):
    customer = Customer(
        merchant_id=current_merchant.id,
        name=request.name.strip(),
        email=request.email.strip().lower(),
        phone=request.phone.strip() if request.phone else None,
        risk_score=request.riskScore,
    )

    await get_customer_repository().insert(customer)

    payments = await get_payment_repository().find_many(
        {
            "customer_id": customer.id,
            "merchant_id": current_merchant.id,
        },
        limit=1000,
    )

    cases = await get_recovery_case_repository().find_many(
        {
            "customer_id": customer.id,
            "merchant_id": current_merchant.id,
        },
        limit=1000,
    )

    return build_customer_dto(
        customer,
        payments,
        cases,
    )


@router.get(
    "",
    response_model=list[CustomerDTO],
    response_model_by_alias=True,
)
async def list_customers(current_merchant: CurrentMerchant):
    customer_repository = get_customer_repository()

    customers = await customer_repository.find_many(
        {
            "merchant_id": current_merchant.id,
        },
        limit=100,
    )

    payments = await get_payment_repository().find_many(
        {
            "merchant_id": current_merchant.id,
        },
        limit=1000,
    )

    cases = await get_recovery_case_repository().find_many(
        {
            "merchant_id": current_merchant.id,
        },
        limit=1000,
    )

    return [
        build_customer_dto(
            customer,
            payments,
            cases,
        )
        for customer in customers
    ]


@router.get(
    "/{customer_id}",
    response_model=CustomerDTO,
    response_model_by_alias=True,
)
async def get_customer(
    customer_id: str,
    current_merchant: CurrentMerchant,
):
    customer = await get_customer_repository().find_one(
        {
            "id": customer_id,
            "merchant_id": current_merchant.id,
        }
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    payments = await get_payment_repository().find_many(
        {
            "customer_id": customer.id,
            "merchant_id": current_merchant.id,
        },
        limit=1000,
    )

    cases = await get_recovery_case_repository().find_many(
        {
            "customer_id": customer.id,
            "merchant_id": current_merchant.id,
        },
        limit=1000,
    )

    return build_customer_dto(
        customer,
        payments,
        cases,
    )