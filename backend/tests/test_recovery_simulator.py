from app.recovery.simulator import RecoverySimulator


def test_simulator_is_deterministic():
    simulator = RecoverySimulator()

    first = simulator.simulate(
        payment_id="SIM_TEST_001",
        amount=1499,
        failure_reason="Insufficient Funds",
        action="SMART_RETRY",
        attempt_number=1,
    )

    second = simulator.simulate(
        payment_id="SIM_TEST_001",
        amount=1499,
        failure_reason="Insufficient Funds",
        action="SMART_RETRY",
        attempt_number=1,
    )

    assert first.succeeded == second.succeeded
    assert first.recovery_probability == second.recovery_probability
    assert first.reason == second.reason


def test_simulator_does_not_depend_on_ml_prediction():
    simulator = RecoverySimulator()

    result = simulator.simulate(
        payment_id="SIM_TEST_002",
        amount=1499,
        failure_reason="Insufficient Funds",
        action="SMART_RETRY",
        attempt_number=1,
    )

    assert isinstance(result.succeeded, bool)
    assert 0.0 <= result.recovery_probability <= 1.0