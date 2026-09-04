import pytest

from app.ml.agent import execute_recovery_case
from app.models.domain import PaymentStatus


@pytest.mark.anyio
async def test_recovered_payment_is_not_retried_or_downgraded(
    monkeypatch,
):
    class FakeRecoveryCase:
        id = "CASE_1"
        payment_id = "PAYMENT_1"
        recovery_probability = 0.20
        recommended_action = "STOP"

    class FakePayment:
        id = "PAYMENT_1"
        status = PaymentStatus.RECOVERED

    class FakeRecoveryCaseRepository:
        async def find_by_id(self, item_id):
            return FakeRecoveryCase()

    class FakePaymentRepository:
        async def find_by_id(self, item_id):
            return FakePayment()

    class FakeUnusedRepository:
        pass

    monkeypatch.setattr(
        "app.ml.agent.get_recovery_case_repository",
        lambda: FakeRecoveryCaseRepository(),
    )

    monkeypatch.setattr(
        "app.ml.agent.get_payment_repository",
        lambda: FakePaymentRepository(),
    )

    monkeypatch.setattr(
        "app.ml.agent.get_payment_attempt_repository",
        lambda: FakeUnusedRepository(),
    )

    monkeypatch.setattr(
        "app.ml.agent.get_audit_log_repository",
        lambda: FakeUnusedRepository(),
    )

    result = await execute_recovery_case("CASE_1")

    assert result is not None
    assert result.id == "CASE_1"