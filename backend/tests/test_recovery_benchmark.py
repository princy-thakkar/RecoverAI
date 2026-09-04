from app.recovery.benchmark import RecoveryBenchmark


def test_benchmark_returns_all_strategies():
    benchmark = RecoveryBenchmark()

    result = benchmark.run(
        batch_size=20,
        seed=2026,
    )

    assert result["synthetic"] is True
    assert result["batch_size"] == 20
    assert len(result["strategies"]) == 3

    strategies = {
        item["strategy"]
        for item in result["strategies"]
    }

    assert strategies == {
        "NEVER_RETRY",
        "RETRY_ALL_ONCE",
        "RECOVERAI",
    }


def test_benchmark_is_deterministic():
    benchmark = RecoveryBenchmark()

    first = benchmark.run(
        batch_size=50,
        seed=2026,
    )

    second = benchmark.run(
        batch_size=50,
        seed=2026,
    )

    assert first == second


def test_benchmark_never_retry_recovers_zero():
    benchmark = RecoveryBenchmark()

    result = benchmark.run(
        batch_size=25,
        seed=2026,
    )

    never_retry = next(
        item
        for item in result["strategies"]
        if item["strategy"] == "NEVER_RETRY"
    )

    assert never_retry["attempts"] == 0
    assert never_retry["successful_recoveries"] == 0
    assert never_retry["revenue_recovered"] == 0.0
    assert never_retry["recovery_rate"] == 0.0


def test_benchmark_revenue_cannot_exceed_revenue_at_risk():
    benchmark = RecoveryBenchmark()

    result = benchmark.run(
        batch_size=100,
        seed=2026,
    )

    for strategy in result["strategies"]:
        assert (
            strategy["revenue_recovered"]
            <= strategy["revenue_at_risk"]
        )


def test_recoverai_reports_control_metrics():
    benchmark = RecoveryBenchmark()

    result = benchmark.run(
        batch_size=100,
        seed=2026,
    )

    recoverai = next(
        item
        for item in result["strategies"]
        if item["strategy"] == "RECOVERAI"
    )

    assert recoverai["automated_actions"] >= 0
    assert recoverai["customer_actions"] >= 0
    assert recoverai["escalations"] >= 0
    assert recoverai["stopped"] >= 0
    assert recoverai["unsafe_actions_blocked"] >= 0