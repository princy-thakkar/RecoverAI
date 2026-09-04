from app.ml.decision import choose_recovery_action


def test_high_probability_selects_smart_retry():
    assert choose_recovery_action(0.9878) == "SMART_RETRY"


def test_medium_probability_selects_reminder():
    assert choose_recovery_action(0.65) == "REMINDER"


def test_low_probability_selects_support_escalation():
    assert choose_recovery_action(0.20) == "SUPPORT_ESCALATION"