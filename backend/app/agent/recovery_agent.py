from __future__ import annotations

from app.agent.decision import choose_recovery_action
from app.ai.reasoning import analyze_recovery_decision
from app.ml.predict import predict_recovery_probability
from app.models.domain import (
    AuditLog,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
    RecoveryCase,
    RecoveryCaseStatus,
    RecommendedAction,
)
from app.repositories.entities import (
    get_audit_log_repository,
    get_payment_attempt_repository,
    get_payment_repository,
    get_recovery_case_repository,
)
from app.policy.engine import evaluate_recovery_action
from app.recovery.simulator import RecoverySimulator


MAX_RECOVERY_ATTEMPTS = 3


async def run_recovery_agent(
    payment_id: str,
    requested_action: RecommendedAction | None = None,
):
    """
    Run the complete RecoverAI recovery workflow.

    Workflow:

        Payment
          ↓
        ML prediction
          ↓
        Decision engine
          ↓
        Policy engine
          ↓
        Recovery action
          ↓
        Audit log
    """

    payment_repository = get_payment_repository()
    recovery_case_repository = get_recovery_case_repository()
    payment_attempt_repository = get_payment_attempt_repository()
    audit_log_repository = get_audit_log_repository()

    # =========================================================
    # 1. Find payment
    # =========================================================

    payment = await payment_repository.find_by_id(payment_id)

    if payment is None:
        return None

    # =========================================================
    # 2. Stop if payment is already successful/recovered
    # =========================================================

    if payment.status in (
        PaymentStatus.SUCCESSFUL,
        PaymentStatus.RECOVERED,
    ):
        reason = (
            "Payment is already successful or recovered. "
            "No further recovery action is required."
        )

        return {
            "payment": payment.model_dump(mode="json"),
            "action": "STOP",
            "recommended_action": "STOP",
            "requested_action": (
                requested_action.value
                if requested_action
                else None
            ),
            "probability": 1.0,
            "reason": reason,
            "success": True,
            "policy_allowed": False,
            "policy_rule": "PAYMENT_ALREADY_RECOVERED",
            "policy_reason": reason,
        }

    # =========================================================
    # 3. Get previous attempts
    # =========================================================

    attempts = await payment_attempt_repository.find_many(
        {"payment_id": payment.id},
        limit=100,
    )

    previous_attempts = len(attempts)

    failed_attempts = sum(
        1
        for attempt in attempts
        if attempt.status == PaymentAttemptStatus.FAILED
    )

    attempt_number = previous_attempts + 1

    # =========================================================
    # 4. Maximum attempt guardrail
    # =========================================================

    if previous_attempts >= MAX_RECOVERY_ATTEMPTS:

        reason = (
            f"Maximum recovery attempts "
            f"({MAX_RECOVERY_ATTEMPTS}) have been reached."
        )

        audit_log = AuditLog(
            payment_id=payment.id,
            action="STOP",
            reason=reason,
            confidence=0.0,
        )

        await audit_log_repository.insert(audit_log)

        return {
            "payment": payment.model_dump(mode="json"),
            "action": "STOP",
            "recommended_action": "STOP",
            "requested_action": (
                requested_action.value
                if requested_action
                else None
            ),
            "probability": 0.0,
            "reason": reason,
            "success": False,
            "policy_allowed": False,
            "policy_rule": "MAX_ATTEMPTS",
            "policy_reason": reason,
            "audit_log": audit_log.model_dump(mode="json"),
        }

    # =========================================================
    # 5. Prepare ML data
    # =========================================================

    payment_data = payment.model_dump()

    payment_data["previous_attempts"] = previous_attempts
    payment_data["failed_attempts"] = failed_attempts

    # =========================================================
    # 6. ML prediction
    # =========================================================

    probability = predict_recovery_probability(
        payment_data
    )

    # =========================================================
    # 7. Decision engine
    # =========================================================

    recommended_action = choose_recovery_action(
        probability=probability,
        failure_reason=payment.failure_reason,
        attempts=previous_attempts,
    )

    # =========================================================
    # 8. Policy engine
    #
    # IMPORTANT:
    #
    # The merchant/user can request an action, but cannot
    # bypass the safety policy.
    #
    # Example:
    #
    # Model recommendation = REMINDER
    # Merchant request       = SMART_RETRY
    #
    # Policy → BLOCK
    # =========================================================

    policy_decision = evaluate_recovery_action(
        recommended_action=recommended_action,
        requested_action=requested_action,
        probability=probability,
        failure_reason=payment.failure_reason,
        attempts=previous_attempts,
        amount=float(payment.amount),
    )

    action = policy_decision.selected_action

    # =========================================================
    # 9. AI explanation
    # =========================================================

    explanation = analyze_recovery_decision(
        payment=payment_data,
        probability=probability,
        recommended_action=recommended_action.value,
    )

    explanation["policy"] = {
        "allowed": policy_decision.allowed,
        "requested_action": (
            requested_action.value
            if requested_action
            else None
        ),
        "selected_action": action.value,
        "rule": policy_decision.rule,
        "reason": policy_decision.reason,
    }

    # =========================================================
    # 10. Find existing recovery case
    #
    # IMPORTANT:
    # Do NOT create duplicate recovery cases.
    # =========================================================

    recovery_case = await recovery_case_repository.find_one(
        {
            "payment_id": payment.id
        }
    )

    # =========================================================
    # 11. Policy blocked
    #
    # Even if the merchant requested an action, the policy
    # engine has the final authority.
    # =========================================================

    if not policy_decision.allowed:

        if recovery_case:

            updated_case = await recovery_case_repository.update_by_id(
                recovery_case.id,
                {
                    "status": RecoveryCaseStatus.FAILED.value,
                    "recovery_probability": probability,
                    "recommended_action": recommended_action.value,
                },
            )

            recovery_case = (
                updated_case
                if updated_case
                else recovery_case
            )

        audit_reason = (
            f"Recovery action blocked by policy. "
            f"Requested action: "
            f"{requested_action.value if requested_action else 'NONE'}. "
            f"Recommended action: {recommended_action.value}. "
            f"Rule: {policy_decision.rule}. "
            f"Reason: {policy_decision.reason}"
        )

        audit_log = AuditLog(
            payment_id=payment.id,
            action="STOP",
            reason=audit_reason,
            confidence=probability,
        )

        await audit_log_repository.insert(audit_log)

        return {
            "payment": payment.model_dump(mode="json"),

            "recovery_case": (
                recovery_case.model_dump(mode="json")
                if recovery_case
                else None
            ),

            "payment_attempt": None,

            "audit_log": audit_log.model_dump(
                mode="json"
            ),

            "probability": probability,

            "action": "STOP",

            "recommended_action": (
                recommended_action.value
            ),

            "requested_action": (
                requested_action.value
                if requested_action
                else None
            ),

            "success": False,

            "policy_allowed": False,
            "policy_rule": policy_decision.rule,
            "policy_reason": policy_decision.reason,

            "action_overridden": (
                requested_action is not None
                and action != requested_action
            ),

            "reason": audit_reason,

            "ai_explanation": explanation,
        }

    # =========================================================
    # 12. Determine recovery case status
    # =========================================================

    if action.value in (
        "REMINDER",
        "PAYMENT_METHOD_SUGGESTION",
    ):

        recovery_case_status = (
            RecoveryCaseStatus.AWAITING_CUSTOMER
        )

    elif action.value == "SUPPORT_ESCALATION":

        recovery_case_status = (
            RecoveryCaseStatus.IN_PROGRESS
        )

    else:

        recovery_case_status = (
            RecoveryCaseStatus.IN_PROGRESS
        )

    # =========================================================
    # 13. Create OR update recovery case
    # =========================================================

    if recovery_case:

        updated_case = await recovery_case_repository.update_by_id(
            recovery_case.id,
            {
                "recovery_probability": probability,
                "recommended_action": recommended_action.value,
                "status": recovery_case_status.value,
            },
        )

        recovery_case = (
            updated_case
            if updated_case
            else recovery_case
        )

    else:

        recovery_case = RecoveryCase(
            payment_id=payment.id,
            customer_id=payment.customer_id,
            recovery_probability=probability,
            status=recovery_case_status,
            recommended_action=recommended_action,
        )

        await recovery_case_repository.insert(
            recovery_case
        )

    # =========================================================
    # 14. Customer-action workflows
    # =========================================================

    if action.value in (
        "REMINDER",
        "PAYMENT_METHOD_SUGGESTION",
        "SUPPORT_ESCALATION",
    ):

        audit_reason = explanation["reasoning"]

        audit_log = AuditLog(
            payment_id=payment.id,
            action=action.value,
            reason=audit_reason,
            confidence=probability,
        )

        await audit_log_repository.insert(
            audit_log
        )

        return {
            "payment": payment.model_dump(mode="json"),

            "recovery_case": recovery_case.model_dump(
                mode="json"
            ),

            "payment_attempt": None,

            "audit_log": audit_log.model_dump(
                mode="json"
            ),

            "probability": probability,

            "action": action.value,

            "recommended_action": (
                recommended_action.value
            ),

            "requested_action": (
                requested_action.value
                if requested_action
                else None
            ),

            "success": True,

            "policy_allowed": True,
            "policy_rule": policy_decision.rule,
            "policy_reason": policy_decision.reason,

            "action_overridden": (
                requested_action is not None
                and action != requested_action
            ),

            "ai_explanation": explanation,
        }

    simulator = RecoverySimulator()
    
    # =========================================================
    # 15. SMART RETRY
    # =========================================================

    if action.value == "SMART_RETRY":

        await payment_repository.update_by_id(
            payment.id,
            {
                "status": PaymentStatus.RECOVERING.value,
            },
        )

        # =====================================================
        # IMPORTANT:
        #
        # This is still the OLD prototype simulation.
        #
        # We will replace this in Phase 2 with an independent
        # ground-truth simulator.
        #
        # DO NOT use this result as benchmark evidence yet.
        # =====================================================

        simulation = simulator.simulate(
            payment_id=payment.id,
            amount=float(payment.amount),
            failure_reason=payment.failure_reason,
            action=action.value,
            attempt_number=attempt_number,
        )

        recovery_succeeded = simulation.succeeded

        if recovery_succeeded:

            attempt_status = PaymentAttemptStatus.SUCCESS
            payment_status = PaymentStatus.RECOVERED
            recovery_status = RecoveryCaseStatus.RECOVERED

            outcome_reason = simulation.reason

            attempt_failure_reason = None

        else:

            attempt_status = PaymentAttemptStatus.FAILED
            payment_status = PaymentStatus.FAILED
            recovery_status = RecoveryCaseStatus.FAILED

            outcome_reason = simulation.reason

            attempt_failure_reason = (
                "Independent recovery simulation unsuccessful"
            )

        # =====================================================
        # Store payment attempt
        # =====================================================

        attempt = PaymentAttempt(
            payment_id=payment.id,
            attempt_number=attempt_number,
            status=attempt_status,
            failure_reason=attempt_failure_reason,
        )

        await payment_attempt_repository.insert(
            attempt
        )

        # =====================================================
        # Update payment
        # =====================================================

        updated_payment = await payment_repository.update_by_id(
            payment.id,
            {
                "status": payment_status.value,
            },
        )

        # =====================================================
        # Update recovery case
        # =====================================================

        updated_case = await recovery_case_repository.update_by_id(
            recovery_case.id,
            {
                "status": recovery_status.value,
                "recovery_probability": probability,
                "recommended_action": recommended_action.value,
            },
        )

        # =====================================================
        # Audit log
        # =====================================================

        audit_log = AuditLog(
            payment_id=payment.id,
            action=action.value,
            reason=outcome_reason,
            confidence=probability,
        )

        await audit_log_repository.insert(
            audit_log
        )

        # =====================================================
        # Return result
        # =====================================================

        return {
            "payment": (
                updated_payment.model_dump(mode="json")
                if updated_payment
                else None
            ),

            "recovery_case": (
                updated_case.model_dump(mode="json")
                if updated_case
                else None
            ),

            "payment_attempt": attempt.model_dump(
                mode="json"
            ),

            "audit_log": audit_log.model_dump(
                mode="json"
            ),

            "probability": probability,

            "action": action.value,

            "recommended_action": (
                recommended_action.value
            ),

            "requested_action": (
                requested_action.value
                if requested_action
                else None
            ),

            "success": recovery_succeeded,

            "policy_allowed": True,
            "policy_rule": policy_decision.rule,
            "policy_reason": policy_decision.reason,

            "action_overridden": (
                requested_action is not None
                and action != requested_action
            ),

            "ai_explanation": explanation,
        }

    # =========================================================
    # 16. Unexpected action safety fallback
    # =========================================================

    reason = (
        f"Unsupported recovery action: {action.value}. "
        "No automated payment action was performed."
    )

    await recovery_case_repository.update_by_id(
        recovery_case.id,
        {
            "status": RecoveryCaseStatus.FAILED.value,
        },
    )

    audit_log = AuditLog(
        payment_id=payment.id,
        action="STOP",
        reason=reason,
        confidence=probability,
    )

    await audit_log_repository.insert(
        audit_log
    )

    return {
        "payment": payment.model_dump(mode="json"),

        "recovery_case": recovery_case.model_dump(
            mode="json"
        ),

        "action": "STOP",

        "probability": probability,

        "reason": reason,

        "success": False,

        "policy_allowed": False,
        "policy_rule": "UNSUPPORTED_ACTION",
        "policy_reason": reason,

        "audit_log": audit_log.model_dump(
            mode="json"
        ),

        "ai_explanation": explanation,
    }