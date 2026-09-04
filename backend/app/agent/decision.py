from __future__ import annotations

from app.models.domain import RecommendedAction


def choose_recovery_action(
    probability: float,
    failure_reason: str | None = None,
    attempts: int = 0,
) -> RecommendedAction:
    """
    Select the safest recovery action based on:
    - ML recovery probability
    - payment failure reason
    - number of previous attempts
    """

    # Safety guardrail
    if attempts >= 3:
        return RecommendedAction.STOP

    reason = (failure_reason or "").lower()

    # Very low probability -> don't waste more attempts
    if probability < 0.30:
        return RecommendedAction.STOP

    # Failure-specific decisions
    if "insufficient" in reason or "limit" in reason:
        if probability >= 0.70:
            return RecommendedAction.PAYMENT_METHOD_SUGGESTION
        return RecommendedAction.REMINDER

    if "expired" in reason or "invalid card" in reason:
        return RecommendedAction.PAYMENT_METHOD_SUGGESTION

    if "network" in reason:
        if probability >= 0.60:
            return RecommendedAction.SMART_RETRY
        return RecommendedAction.REMINDER

    if "authentication" in reason:
        return RecommendedAction.PAYMENT_METHOD_SUGGESTION

    if "bank declined" in reason:
        if probability >= 0.70:
            return RecommendedAction.REMINDER
        return RecommendedAction.SUPPORT_ESCALATION

    if "fraud" in reason:
        return RecommendedAction.STOP

    # General probability-based fallback
    if probability >= 0.80:
        return RecommendedAction.SMART_RETRY

    if probability >= 0.50:
        return RecommendedAction.REMINDER

    if probability >= 0.30:
        return RecommendedAction.SUPPORT_ESCALATION

    return RecommendedAction.STOP