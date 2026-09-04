"""
Recovery agent for RecoverAI.

The agent executes a recovery case using a simulated payment retry.
No real payment gateway is called at this stage.
"""

from app.models.domain import (
    AuditLog,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
    RecoveryCaseStatus,
)
from app.repositories.entities import (
    get_audit_log_repository,
    get_payment_attempt_repository,
    get_payment_repository,
    get_recovery_case_repository,
)


async def execute_recovery_case(recovery_case_id: str):
    """
    Execute a recovery case using a simulated recovery attempt.

    Returns the updated recovery case.
    """

    recovery_case_repository = get_recovery_case_repository()
    payment_repository = get_payment_repository()
    payment_attempt_repository = get_payment_attempt_repository()
    audit_log_repository = get_audit_log_repository()

    # 1. Find recovery case
    recovery_case = await recovery_case_repository.find_by_id(
        recovery_case_id
    )

    if recovery_case is None:
        return None

    # 2. Find associated payment
    payment = await payment_repository.find_by_id(
        recovery_case.payment_id
    )

    if payment is None:
        return None
    
    # Do not retry an already recovered payment.
    if payment.status == PaymentStatus.RECOVERED:
        return recovery_case

    # 3. Mark recovery case as in progress
    recovery_case = await recovery_case_repository.update_by_id(
        recovery_case.id,
        {
            "status": RecoveryCaseStatus.IN_PROGRESS.value,
        },
    )

    # 4. Determine next attempt number
    existing_attempts = await payment_attempt_repository.find_many(
        {"payment_id": payment.id},
        limit=100,
    )

    attempt_number = len(existing_attempts) + 1

    # 5. Simulate the recovery attempt.
    #
    # For this stage, a high recovery probability means success.
    attempt_succeeded = recovery_case.recovery_probability >= 0.80

    if attempt_succeeded:
        attempt_status = PaymentAttemptStatus.SUCCESS
        payment_status = PaymentStatus.RECOVERED
        recovery_status = RecoveryCaseStatus.RECOVERED
        reason = (
            "Recovery retry succeeded because the predicted "
            "recovery probability was high."
        )
    else:
        attempt_status = PaymentAttemptStatus.FAILED
        payment_status = PaymentStatus.FAILED
        recovery_status = RecoveryCaseStatus.FAILED
        reason = (
            "Recovery retry failed because the predicted "
            "recovery probability was below the success threshold."
        )

    # 6. Store payment attempt
    attempt = PaymentAttempt(
        payment_id=payment.id,
        attempt_number=attempt_number,
        status=attempt_status,
        failure_reason=None if attempt_succeeded else reason,
    )

    await payment_attempt_repository.insert(attempt)

    # 7. Update payment status
    await payment_repository.update_by_id(
        payment.id,
        {
            "status": payment_status.value,
        },
    )

    # 8. Update recovery case
    updated_case = await recovery_case_repository.update_by_id(
        recovery_case.id,
        {
            "status": recovery_status.value,
        },
    )

    # 9. Create audit log
    audit_log = AuditLog(
        payment_id=payment.id,
        action=recovery_case.recommended_action.value,
        reason=reason,
        confidence=recovery_case.recovery_probability,
    )

    await audit_log_repository.insert(audit_log)

    return updated_case