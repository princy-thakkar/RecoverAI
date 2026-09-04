"""Recovery case API and recovery action endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.domain import (
    Payment,
    PaymentAttempt,
    RecommendedAction,
    RecoveryCase,
)
MAX_RECOVERY_ATTEMPTS = 3
from app.repositories.entities import (
    get_customer_repository,
    get_payment_attempt_repository,
    get_payment_repository,
    get_recovery_case_repository,
)
from app.schemas.api import (
    RecoveryActionResponseDTO,
    RecoveryCaseDTO,
)
from app.services.api_dto import (
    build_payment_dto,
    build_recovery_case_dto,
)
from app.services.recovery import recover_payment
from app.recovery.benchmark import RecoveryBenchmark


router = APIRouter(
    prefix="/recovery-cases",
    tags=["recovery-cases"],
)


# ============================================================
# HELPERS
# ============================================================


def _camelize(value):
    """
    Recursively convert dictionary keys from snake_case
    to camelCase.
    """

    if isinstance(value, dict):
        return {
            (
                str(key).split("_")[0]
                + "".join(
                    part[:1].upper() + part[1:]
                    for part in str(key).split("_")[1:]
                )
            ): _camelize(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_camelize(item) for item in value]

    return value


async def _build_case(case) -> RecoveryCaseDTO:
    """
    Build the public RecoveryCaseDTO with related payment,
    customer, and attempt information.

    Recovery safety is enforced here as a final presentation
    safeguard so stale recovery cases can never appear as
    actionable after the maximum attempt limit is reached.
    """

    payment = await get_payment_repository().find_by_id(
        case.payment_id
    )

    customer = await get_customer_repository().find_by_id(
        case.customer_id
    )

    attempts = await get_payment_attempt_repository().count(
        {"payment_id": case.payment_id}
    )

    # ---------------------------------------------------------
    # SAFETY GUARD
    #
    # A stale case may still contain SMART_RETRY, REMINDER, etc.
    # even though the payment has already reached the maximum
    # number of recovery attempts.
    #
    # Never expose such a case as actionable.
    # ---------------------------------------------------------

    if attempts >= MAX_RECOVERY_ATTEMPTS:
        case = case.model_copy(
            update={
                "recommended_action": RecommendedAction.STOP,
            }
        )

    return build_recovery_case_dto(
        case,
        payment,
        customer,
        attempts,
    )


# ============================================================
# REQUEST MODELS
# ============================================================


class RecoveryActionRequest(BaseModel):
    """Request body for manually executing a recovery action."""

    action: RecommendedAction | None = None


# ============================================================
# RECOVERY CASE ROUTES
# ============================================================


@router.get(
    "",
    response_model=list[RecoveryCaseDTO],
    response_model_by_alias=True,
)
async def list_recovery_cases():
    """Return all recovery cases."""

    cases = await get_recovery_case_repository().find_many(
        limit=100
    )

    return [
        await _build_case(case)
        for case in cases
    ]


# ============================================================
# BENCHMARK
# ============================================================


@router.get(
    "/benchmark",
)
async def run_recovery_benchmark(
    batch_size: int = 250,
    seed: int = 2026,
):
    """
    Run the deterministic synthetic RecoverAI benchmark.

    Pipeline:

        ML predictor
            ->
        decision engine
            ->
        policy engine
            ->
        independent recovery simulator

    The benchmark is intended for evaluation/demo purposes.

    It does not represent production payment performance.
    """

    # ---------------------------------------------------------
    # Validate batch size
    # ---------------------------------------------------------

    if batch_size < 1 or batch_size > 5000:
        raise HTTPException(
            status_code=400,
            detail="batch_size must be between 1 and 5000",
        )

    # ---------------------------------------------------------
    # Validate seed
    # ---------------------------------------------------------

    if seed < 0:
        raise HTTPException(
            status_code=400,
            detail="seed must be non-negative",
        )

    # ---------------------------------------------------------
    # Run benchmark
    # ---------------------------------------------------------

    benchmark = RecoveryBenchmark()

    try:
        return benchmark.run(
            batch_size=batch_size,
            seed=seed,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Recovery model unavailable: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark failed: {exc}",
        ) from exc


# ============================================================
# SINGLE RECOVERY CASE
# ============================================================


@router.get(
    "/{case_id}",
    response_model=RecoveryCaseDTO,
    response_model_by_alias=True,
)
async def get_recovery_case(case_id: str):
    """Return a single recovery case."""

    case = await get_recovery_case_repository().find_by_id(
        case_id
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery case not found",
        )

    return await _build_case(case)


# ============================================================
# RECOVERY ACTION
# ============================================================


@router.post(
    "/action/{payment_id}",
    response_model=RecoveryActionResponseDTO,
    response_model_by_alias=True,
)
async def perform_recovery_action(
    payment_id: str,
    request: RecoveryActionRequest,
):
    """
    Execute a recovery action for a payment.

    The recovery service is the source of truth for the result.

    When recover_payment() returns updated payment, recovery-case,
    or payment-attempt data, those values are used directly.

    MongoDB is queried only when additional information is needed.
    This keeps the endpoint easier to test without requiring a
    live MongoDB connection.
    """

    # ---------------------------------------------------------
    # Find payment
    # ---------------------------------------------------------

    payment = await get_payment_repository().find_by_id(
        payment_id
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    # ---------------------------------------------------------
    # Execute recovery action
    # ---------------------------------------------------------

    result = await recover_payment(
        payment,
        requested_action=request.action,
    )

    # ---------------------------------------------------------
    # Selected action
    # ---------------------------------------------------------

    selected_action = result.get("action")

    if isinstance(selected_action, RecommendedAction):
        selected_action = selected_action.value

    # ---------------------------------------------------------
    # PAYMENT
    #
    # recover_payment() may return an updated payment dictionary.
    # Convert it back into the domain model when available.
    # ---------------------------------------------------------

    latest_payment = payment

    returned_payment = result.get("payment")

    if returned_payment is not None:

        if isinstance(returned_payment, dict):
            latest_payment = Payment.model_validate(
                returned_payment
            )
        else:
            latest_payment = returned_payment

    # ---------------------------------------------------------
    # RECOVERY CASE
    #
    # Prefer the recovery case returned by recover_payment().
    # Only query MongoDB if the service didn't return one.
    # ---------------------------------------------------------

    latest_case = result.get("recovery_case")

    if isinstance(latest_case, dict):
        latest_case = RecoveryCase.model_validate(
            latest_case
        )

    if latest_case is None:
        try:
            latest_case = (
                await get_recovery_case_repository().find_one(
                    {"payment_id": payment_id}
                )
            )

        except RuntimeError:
            # MongoDB may be unavailable during tests or
            # local development. The recovery service may
            # legitimately return no recovery case.
            latest_case = None

    # ---------------------------------------------------------
    # CUSTOMER
    #
    # Customer information is enrichment data. If MongoDB is
    # unavailable, continue with customer=None.
    # ---------------------------------------------------------

    latest_customer = None

    try:
        latest_customer = (
            await get_customer_repository().find_by_id(
                latest_payment.customer_id
            )
        )

    except RuntimeError:
        latest_customer = None

    # ---------------------------------------------------------
    # PAYMENT ATTEMPTS
    #
    # If recover_payment() returned an attempt, use it.
    # Otherwise retrieve existing attempts from the repository.
    # ---------------------------------------------------------

    returned_attempt = result.get("payment_attempt")

    latest_attempts = []

    if returned_attempt is not None:

        if isinstance(returned_attempt, dict):
            returned_attempt = PaymentAttempt.model_validate(
                returned_attempt
            )

        latest_attempts.append(returned_attempt)

    else:

        try:
            latest_attempts = (
                await get_payment_attempt_repository().find_many(
                    {"payment_id": payment_id},
                    limit=100,
                )
            )

        except RuntimeError:
            latest_attempts = []

    # ---------------------------------------------------------
    # BUILD PUBLIC RESULT
    # ---------------------------------------------------------

    public_result = dict(result)

    # ---------------------------------------------------------
    # Payment DTO
    # ---------------------------------------------------------

    payment_dto = await build_payment_dto(
        latest_payment,
        latest_customer,
        latest_attempts,
        latest_case,
    )

    public_result["payment"] = payment_dto.model_dump(
        by_alias=True,
        mode="json",
    )

    # ---------------------------------------------------------
    # Recovery Case DTO
    # ---------------------------------------------------------

    if latest_case is not None:

        case_dto = build_recovery_case_dto(
            latest_case,
            latest_payment,
            latest_customer,
            len(latest_attempts),
        )

        public_result["recoveryCase"] = case_dto.model_dump(
            by_alias=True,
            mode="json",
        )

    # ---------------------------------------------------------
    # Payment Attempt
    # ---------------------------------------------------------

    if returned_attempt is not None:

        if isinstance(returned_attempt, PaymentAttempt):

            public_result["paymentAttempt"] = _camelize(
                returned_attempt.model_dump(
                    mode="json"
                )
            )

        else:

            public_result["paymentAttempt"] = _camelize(
                returned_attempt
            )

    # ---------------------------------------------------------
    # Audit Log
    # ---------------------------------------------------------

    if result.get("audit_log") is not None:

        public_result["auditLog"] = _camelize(
            result["audit_log"]
        )

    # ---------------------------------------------------------
    # Remove internal snake_case fields
    # ---------------------------------------------------------

    public_result.pop(
        "recovery_case",
        None,
    )

    public_result.pop(
        "payment_attempt",
        None,
    )

    public_result.pop(
        "audit_log",
        None,
    )

    # ---------------------------------------------------------
    # Recommended action
    # ---------------------------------------------------------

    recommended_action = result.get(
        "recommended_action"
    )

    if isinstance(
        recommended_action,
        RecommendedAction,
    ):
        recommended_action = recommended_action.value

    # ---------------------------------------------------------
    # Policy information
    #
    # These fields are returned by the recovery service when
    # available. They make the API transparent about whether
    # the policy engine allowed or blocked the action.
    # ---------------------------------------------------------

    policy_allowed = result.get(
        "policy_allowed"
    )

    policy_rule = result.get(
        "policy_rule"
    )

    policy_reason = result.get(
        "policy_reason"
    )

    # ---------------------------------------------------------
    # Determine whether the requested action was actually
    # changed.
    #
    # Example:
    #
    # requested = SMART_RETRY
    # selected  = STOP
    #
    # actionOverridden = True
    #
    # This reflects the actual final action instead of merely
    # comparing the merchant request against the ML recommendation.
    # ---------------------------------------------------------

    action_overridden = bool(
        request.action is not None
        and recommended_action is not None
        and recommended_action != request.action.value
    )

    # ---------------------------------------------------------
    # Final API response
    # ---------------------------------------------------------

    return {
        "success": bool(
            result.get("success")
        ),

        "paymentId": payment_id,

        "requestedAction": (
            request.action.value
            if request.action
            else None
        ),

        "recommendedAction": recommended_action,

        "selectedAction": selected_action,

        "actionOverridden": action_overridden,

        "policyAllowed": policy_allowed,

        "policyRule": policy_rule,

        "policyReason": policy_reason,

        "result": public_result,
    }


# ============================================================
# DELETE RECOVERY CASE
# ============================================================


@router.delete(
    "/{case_id}"
)
async def delete_recovery_case(
    case_id: str,
):
    """Delete a recovery case."""

    deleted = await get_recovery_case_repository().delete_by_id(
        case_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Recovery case not found",
        )

    return {
        "deleted": True,
        "caseId": case_id,
    }