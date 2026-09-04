from app.models.domain import RecommendedAction
from app.policy.engine import evaluate_recovery_action


def test_blocks_retry_after_max_attempts():
    decision = evaluate_recovery_action(
        recommended_action=RecommendedAction.SMART_RETRY,
        requested_action=RecommendedAction.SMART_RETRY,
        probability=0.95,
        failure_reason="insufficient_funds",
        attempts=3,
        amount=1000,
    )

    assert decision.allowed is False
    assert decision.selected_action == RecommendedAction.STOP
    assert decision.rule == "MAX_ATTEMPTS"


def test_blocks_merchant_escalation():
    decision = evaluate_recovery_action(
        recommended_action=RecommendedAction.REMINDER,
        requested_action=RecommendedAction.SMART_RETRY,
        probability=0.95,
        failure_reason="insufficient_funds",
        attempts=0,
        amount=1000,
    )

    assert decision.allowed is False
    assert decision.selected_action == RecommendedAction.STOP
    assert decision.rule == "NO_RISK_ESCALATION"


def test_blocks_low_probability_retry():
    decision = evaluate_recovery_action(
        recommended_action=RecommendedAction.SMART_RETRY,
        requested_action=RecommendedAction.SMART_RETRY,
        probability=0.65,
        failure_reason="insufficient_funds",
        attempts=0,
        amount=1000,
    )

    assert decision.allowed is False
    assert decision.selected_action == RecommendedAction.STOP
    assert decision.rule == "RETRY_PROBABILITY"


def test_blocks_small_automation_amount():
    decision = evaluate_recovery_action(
        recommended_action=RecommendedAction.SMART_RETRY,
        requested_action=RecommendedAction.SMART_RETRY,
        probability=0.95,
        failure_reason="insufficient_funds",
        attempts=0,
        amount=50,
    )

    assert decision.allowed is False
    assert decision.selected_action == RecommendedAction.STOP
    assert decision.rule == "MIN_AUTOMATION_AMOUNT"


def test_allows_valid_smart_retry():
    decision = evaluate_recovery_action(
        recommended_action=RecommendedAction.SMART_RETRY,
        requested_action=RecommendedAction.SMART_RETRY,
        probability=0.95,
        failure_reason="insufficient_funds",
        attempts=0,
        amount=1000,
    )

    assert decision.allowed is True
    assert decision.selected_action == RecommendedAction.SMART_RETRY
    assert decision.rule == "ALLOW"