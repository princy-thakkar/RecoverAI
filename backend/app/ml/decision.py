from __future__ import annotations

from app.models.domain import RecommendedAction


MAX_RECOVERY_ATTEMPTS = 3

HIGH_RECOVERY_THRESHOLD = 0.80
MEDIUM_RECOVERY_THRESHOLD = 0.50
LOW_RECOVERY_THRESHOLD = 0.30

# Transient failures can justify a controlled retry at a lower
# probability threshold because the failure itself is potentially
# temporary rather than a persistent payment-method problem.
TRANSIENT_RETRY_THRESHOLD = 0.60


def choose_recovery_action(
    probability: float,
    failure_reason: str | None = None,
    attempts: int = 0,
) -> RecommendedAction:
    """
    Select a recovery action using ML probability plus failure context.

    The decision engine chooses the recommended action. The policy
    engine remains the final safety gate and may block the action.

    Rules:
    - Stop after the maximum number of attempts.
    - Never retry known-invalid/expired cards.
    - Allow lower-probability retries for transient failures.
    - Use customer-action flows for payment-method problems.
    """

    # ---------------------------------------------------------
    # 1. SAFETY GUARDRAIL
    # ---------------------------------------------------------

    if attempts >= MAX_RECOVERY_ATTEMPTS:
        return RecommendedAction.STOP

    # ---------------------------------------------------------
    # 2. NORMALIZE PROBABILITY
    # ---------------------------------------------------------

    probability = max(0.0, min(1.0, float(probability)))

    reason = (failure_reason or "").strip().lower()

    # ---------------------------------------------------------
    # 3. PAYMENT-METHOD PROBLEMS
    # ---------------------------------------------------------
    # These should not trigger an automated retry of the same
    # payment method.

    if (
        "expired" in reason
        or "invalid card" in reason
        or "card expired" in reason
        or "authentication" in reason
    ):
        if probability < LOW_RECOVERY_THRESHOLD:
            return RecommendedAction.SUPPORT_ESCALATION

        return RecommendedAction.PAYMENT_METHOD_SUGGESTION

    # ---------------------------------------------------------
    # 4. INSUFFICIENT FUNDS
    # ---------------------------------------------------------
    # A sufficiently strong prediction can justify one controlled
    # retry. Otherwise ask the customer to take action.

    if "insufficient" in reason:
        if probability >= 0.75:
            return RecommendedAction.SMART_RETRY

        if probability >= MEDIUM_RECOVERY_THRESHOLD:
            return RecommendedAction.REMINDER

        return RecommendedAction.SUPPORT_ESCALATION

    # ---------------------------------------------------------
    # 5. TRANSIENT FAILURES
    # ---------------------------------------------------------
    # Timeout/network failures may resolve without customer
    # intervention, so the retry threshold is lower.

    if "timeout" in reason or "network" in reason:
        if probability >= TRANSIENT_RETRY_THRESHOLD:
            return RecommendedAction.SMART_RETRY

        if probability >= MEDIUM_RECOVERY_THRESHOLD:
            return RecommendedAction.REMINDER

        return RecommendedAction.SUPPORT_ESCALATION

    # ---------------------------------------------------------
    # 6. BANK DECLINES / OTHER UNKNOWN FAILURES
    # ---------------------------------------------------------

    if probability < LOW_RECOVERY_THRESHOLD:
        return RecommendedAction.SUPPORT_ESCALATION

    if probability >= HIGH_RECOVERY_THRESHOLD:
        return RecommendedAction.SMART_RETRY

    if probability >= MEDIUM_RECOVERY_THRESHOLD:
        return RecommendedAction.REMINDER

    return RecommendedAction.SUPPORT_ESCALATION