from __future__ import annotations

from dataclasses import dataclass

from app.models.domain import RecommendedAction

MAX_RECOVERY_ATTEMPTS = 3

# Context-aware retry thresholds.
DEFAULT_SMART_RETRY_MIN_PROBABILITY = 0.80
TRANSIENT_SMART_RETRY_MIN_PROBABILITY = 0.60

# Never automate very small recoveries.
MIN_AUTOMATION_AMOUNT = 100.0

ACTION_RISK = {
    RecommendedAction.STOP: 0,
    RecommendedAction.REMINDER: 1,
    RecommendedAction.PAYMENT_METHOD_SUGGESTION: 1,
    RecommendedAction.SUPPORT_ESCALATION: 1,
    RecommendedAction.SMART_RETRY: 2,
}


@dataclass
class PolicyDecision:
    allowed: bool
    selected_action: RecommendedAction
    requested_action: RecommendedAction | None
    reason: str
    rule: str


def _is_transient_failure(reason: str) -> bool:
    return "timeout" in reason or "network" in reason


def _is_non_retryable_failure(reason: str) -> bool:
    non_retryable = (
        "expired",
        "invalid card",
        "card expired",
        "fraud",
        "stolen",
        "blocked",
        "authentication",
    )
    return any(term in reason for term in non_retryable)


def evaluate_recovery_action(
    *,
    recommended_action: RecommendedAction,
    requested_action: RecommendedAction | None,
    probability: float,
    failure_reason: str | None,
    attempts: int,
    amount: float,
) -> PolicyDecision:

    reason = (failure_reason or "").strip().lower()

    # Hard stopping rule.
    if attempts >= MAX_RECOVERY_ATTEMPTS:
        return PolicyDecision(
            allowed=False,
            selected_action=RecommendedAction.STOP,
            requested_action=requested_action,
            reason="Maximum recovery attempts reached.",
            rule="MAX_ATTEMPTS",
        )

    candidate_action = (
        requested_action
        if requested_action is not None
        else recommended_action
    )

    # Merchant/frontend requests may downgrade the model recommendation,
    # but may never escalate it to a riskier action.
    if ACTION_RISK[candidate_action] > ACTION_RISK[recommended_action]:
        return PolicyDecision(
            allowed=False,
            selected_action=RecommendedAction.STOP,
            requested_action=requested_action,
            reason="Requested action exceeds the model-recommended risk level.",
            rule="NO_RISK_ESCALATION",
        )

    if candidate_action != RecommendedAction.SMART_RETRY:
        return PolicyDecision(
            allowed=True,
            selected_action=candidate_action,
            requested_action=requested_action,
            reason="Action is within the recovery policy.",
            rule="ALLOW",
        )

    # SMART_RETRY safety checks.
    if _is_non_retryable_failure(reason):
        return PolicyDecision(
            allowed=False,
            selected_action=RecommendedAction.STOP,
            requested_action=requested_action,
            reason="Failure reason is not safe for automated retry.",
            rule="NON_RETRYABLE_FAILURE",
        )

    if amount < MIN_AUTOMATION_AMOUNT:
        return PolicyDecision(
            allowed=False,
            selected_action=RecommendedAction.STOP,
            requested_action=requested_action,
            reason="Amount is below the minimum automation threshold.",
            rule="MIN_AUTOMATION_AMOUNT",
        )

    probability = max(0.0, min(1.0, float(probability)))

    retry_threshold = (
        TRANSIENT_SMART_RETRY_MIN_PROBABILITY
        if _is_transient_failure(reason)
        else DEFAULT_SMART_RETRY_MIN_PROBABILITY
    )

    if probability < retry_threshold:
        return PolicyDecision(
            allowed=False,
            selected_action=RecommendedAction.STOP,
            requested_action=requested_action,
            reason=(
                f"Recovery probability {probability:.2f} is below "
                f"the {retry_threshold:.2f} retry threshold."
            ),
            rule="RETRY_PROBABILITY",
        )

    return PolicyDecision(
        allowed=True,
        selected_action=RecommendedAction.SMART_RETRY,
        requested_action=requested_action,
        reason="Automated retry passed all policy checks.",
        rule="ALLOW",
    )