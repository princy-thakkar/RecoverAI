"""
ML prediction endpoints for RecoverAI.

Stage 4:
- Predict recovery probability.
- Choose a recovery action.
- Create and persist recovery cases.
"""
from app.ml.agent import execute_recovery_case
from app.agent.recovery_agent import run_recovery_agent
from fastapi import APIRouter, HTTPException

from app.ml.decision import choose_recovery_action
from app.ml.predict import predict_recovery_probability
from app.models.domain import RecoveryCase
from app.repositories.entities import (
    get_payment_repository,
    get_recovery_case_repository,
)
from app.schemas.ml import RecoveryPredictionRequest


router = APIRouter(
    prefix="/ml",
    tags=["machine-learning"],
)


@router.post("/predict-recovery")
async def predict_recovery(request: RecoveryPredictionRequest):
    """
    Predict recovery probability and recommended action
    from supplied payment information.
    """

    payment = request.model_dump()

    probability = predict_recovery_probability(payment)
    action = choose_recovery_action(probability)

    return {
        "recovery_probability": probability,
        "recommended_action": action,
    }


@router.post("/predict-recovery/{payment_id}")
async def predict_recovery_for_payment(payment_id: str):
    """
    Predict recovery probability and recommended action
    for an existing MongoDB payment.
    """

    payment_repository = get_payment_repository()

    payment = await payment_repository.find_by_id(payment_id)

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    payment_data = payment.model_dump()

    probability = predict_recovery_probability(payment_data)
    action = choose_recovery_action(probability)

    return {
        "payment_id": payment.id,
        "recovery_probability": probability,
        "recommended_action": action,
    }


@router.post("/create-recovery-case/{payment_id}")
async def create_recovery_case(payment_id: str):
    """
    Predict recovery for a payment and create a recovery case
    in MongoDB.
    """

    payment_repository = get_payment_repository()

    payment = await payment_repository.find_by_id(payment_id)

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    # Safety guardrail: never create a recovery case
    # for an already successful or recovered payment.
    if payment.status.value in (
        "successful",
        "recovered",
    ):
        return {
            "payment": payment.model_dump(mode="json"),
            "action": "STOP",
            "reason": "Payment is already recovered or successful.",
        }



    # Check for an active recovery case for this payment.
    recovery_case_repository = get_recovery_case_repository()

    existing_cases = await recovery_case_repository.find_many(
        {
            "payment_id": payment.id,
            "status": {
                "$in": [
                    "pending",
                    "in_progress",
                    "awaiting_customer",
                    "retry_scheduled",
                ]
            },
        },
        limit=1,
    )

    if existing_cases:
        return existing_cases[0].model_dump(mode="json")

    payment_data = payment.model_dump()

    probability = predict_recovery_probability(payment_data)
    action = choose_recovery_action(probability)

    recovery_case = RecoveryCase(
        payment_id=payment.id,
        customer_id=payment.customer_id,
        recovery_probability=probability,
        status="pending",
        recommended_action=action,
    )

    await recovery_case_repository.insert(recovery_case)

    return recovery_case.model_dump(mode="json")

@router.post("/execute-recovery/{recovery_case_id}")
async def execute_recovery(recovery_case_id: str):
    """
    Execute a recovery case using the recovery agent.
    """

    recovery_case = await execute_recovery_case(recovery_case_id)

    if recovery_case is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery case or payment not found",
        )

    return recovery_case.model_dump(mode="json")

@router.post("/run-recovery-agent/{payment_id}")
async def run_recovery(payment_id: str):
    """
    Run the automated recovery agent for a payment.
    """

    result = await run_recovery_agent(payment_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return result