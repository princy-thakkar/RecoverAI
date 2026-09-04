"""Phase 2 recovery workflow and public API contract tests."""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.domain import (
    AuditLog,
    Customer,
    Payment,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
    RecommendedAction,
    RecoveryCase,
    RecoveryCaseStatus,
)
from app.agent.recovery_agent import MAX_RECOVERY_ATTEMPTS, run_recovery_agent
from app.recovery.simulator import RecoverySimulationResult
from app.api.auth import get_current_merchant


NOW = datetime.now(timezone.utc)
client = TestClient(app)

async def fake_current_merchant():
    return type(
        "TestMerchant",
        (),
        {
            "id": "MERCHANT_1",
        },
    )()


app.dependency_overrides[get_current_merchant] = fake_current_merchant


class MemoryPaymentRepository:
    def __init__(self, payment: Payment):
        self.payment = payment

    async def find_one(self, filter_query=None):
        """Match the production repository contract with merchant isolation."""
        if not filter_query:
            return self.payment

        if filter_query.get("id") != self.payment.id:
            return None

        if filter_query.get("merchant_id") != self.payment.merchant_id:
            return None

        return self.payment

    async def find_by_id(self, item_id):
        return self.payment if item_id == self.payment.id else None

    async def find_many(self, filter_query=None, limit=100):
        filter_query = filter_query or {}

        if "merchant_id" in filter_query:
            if filter_query["merchant_id"] != self.payment.merchant_id:
                return []

        if "id" in filter_query:
            if filter_query["id"] != self.payment.id:
                return []

        return [self.payment][:limit]

    async def update_by_id(self, item_id, updates):
        if item_id != self.payment.id:
            return None

        for key, value in updates.items():
            setattr(self.payment, key, value)

        return self.payment


class MemoryAttemptRepository:
    def __init__(self, attempts=None):
        self.attempts = list(attempts or [])

    async def find_many(self, filter_query=None, limit=100):
        payment_id = (filter_query or {}).get("payment_id")

        if payment_id is None:
            return self.attempts[:limit]

        return [
            attempt
            for attempt in self.attempts
            if attempt.payment_id == payment_id
        ][:limit]

    async def count(self, filter_query=None):
        return len(await self.find_many(filter_query))

    async def insert(self, attempt):
        self.attempts.append(attempt)
        return attempt


class MemoryRecoveryRepository:
    def __init__(self, case=None):
        self.case = case

    async def find_one(self, filter_query):
        if not self.case:
            return None

        if filter_query.get("payment_id") != self.case.payment_id:
            return None

        return self.case

    async def find_by_id(self, item_id):
        return (
            self.case
            if self.case and self.case.id == item_id
            else None
        )

    async def find_many(self, filter_query=None, limit=100):
        if not self.case:
            return []

        filter_query = filter_query or {}

        if "payment_id" in filter_query:
            if filter_query["payment_id"] != self.case.payment_id:
                return []

        if "status" in filter_query:
            status_filter = filter_query["status"]

            if isinstance(status_filter, dict):
                allowed = status_filter.get("$in", [])
                case_status = (
                    self.case.status.value
                    if hasattr(self.case.status, "value")
                    else str(self.case.status)
                )

                if allowed and case_status not in allowed:
                    return []

        return [self.case][:limit]

    async def insert(self, case):
        self.case = case
        return case

    async def update_by_id(self, item_id, updates):
        if not self.case or self.case.id != item_id:
            return None

        for key, value in updates.items():
            setattr(self.case, key, value)

        self.case.updated_at = NOW
        return self.case


class MemoryAuditRepository:
    def __init__(self):
        self.logs = []

    async def insert(self, item: AuditLog):
        self.logs.append(item)
        return item


class MemoryCustomerRepository:
    def __init__(self, customer: Customer):
        self.customer = customer

    async def find_by_id(self, item_id):
        return (
            self.customer
            if item_id == self.customer.id
            else None
        )

    async def find_many(self, filter_query=None, limit=100):
        filter_query = filter_query or {}

        if "merchant_id" in filter_query:
            if filter_query["merchant_id"] != self.customer.merchant_id:
                return []

        if "id" in filter_query:
            if filter_query["id"] != self.customer.id:
                return []

        return [self.customer][:limit]


def make_payment(status=PaymentStatus.FAILED):
    return Payment(
        id="PAYMENT_PHASE2",
        merchant_id="MERCHANT_1",
        customer_id="CUSTOMER_1",
        amount=1499,
        currency="INR",
        status=status,
        payment_method="UPI",
        failure_reason="Insufficient Funds",
        created_at=NOW,
    )


def make_case(
    action=RecommendedAction.SMART_RETRY,
    status=RecoveryCaseStatus.PENDING,
):
    return RecoveryCase(
        id="CASE_PHASE2",
        payment_id="PAYMENT_PHASE2",
        customer_id="CUSTOMER_1",
        recovery_probability=0.91,
        status=status,
        recommended_action=action,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def recovery_repositories(monkeypatch):
    payment = make_payment()

    customer = Customer(
        id="CUSTOMER_1",
        merchant_id="MERCHANT_1",
        name="Phase 2 Customer",
        email="phase2@example.com",
        phone="+91 90000 00001",
        risk_score=0.40,
        created_at=NOW,
    )

    payments = MemoryPaymentRepository(payment)
    attempts = MemoryAttemptRepository()
    recovery = MemoryRecoveryRepository()
    audit = MemoryAuditRepository()
    customers = MemoryCustomerRepository(customer)

    monkeypatch.setattr(
        "app.agent.recovery_agent.get_payment_repository",
        lambda: payments,
    )
    monkeypatch.setattr(
        "app.agent.recovery_agent.get_payment_attempt_repository",
        lambda: attempts,
    )
    monkeypatch.setattr(
        "app.agent.recovery_agent.get_recovery_case_repository",
        lambda: recovery,
    )
    monkeypatch.setattr(
        "app.agent.recovery_agent.get_audit_log_repository",
        lambda: audit,
    )
    monkeypatch.setattr(
        "app.agent.recovery_agent.predict_recovery_probability",
        lambda _: 0.91,
    )
    monkeypatch.setattr(
        "app.agent.recovery_agent.choose_recovery_action",
        lambda **_: RecommendedAction.SMART_RETRY,
    )
    monkeypatch.setattr(
        "app.agent.recovery_agent.analyze_recovery_decision",
        lambda **_: {
            "probability": 0.91,
            "probabilityPercent": 91.0,
            "riskLevel": "LOW",
            "recommendedAction": "SMART_RETRY",
            "summary": "High recovery potential.",
            "reasoning": "A controlled retry is recommended.",
            "nextStep": "Perform one controlled recovery retry.",
            "paymentAmount": 1499.0,
            "paymentMethod": "UPI",
            "failureReason": "Insufficient Funds",
            "previousAttempts": 0,
            "failedAttempts": 0,
        },
    )

    return payments, attempts, recovery, audit, customers


@pytest.mark.anyio
async def test_recovery_case_is_created_and_reused(
    recovery_repositories,
):
    _, attempts, recovery, _, _ = recovery_repositories

    first = await run_recovery_agent(
        "PAYMENT_PHASE2",
        requested_action=RecommendedAction.REMINDER,
    )

    second = await run_recovery_agent(
        "PAYMENT_PHASE2",
        requested_action=RecommendedAction.REMINDER,
    )

    assert first["recovery_case"]["id"] == second["recovery_case"]["id"]
    assert len(attempts.attempts) == 0
    assert first["action"] == "REMINDER"
    assert second["action"] == "REMINDER"
    assert recovery.case is not None


@pytest.mark.anyio
async def test_merchant_action_is_executed_while_recommendation_is_preserved(
    recovery_repositories,
    monkeypatch,
):
    payment_repo, attempts, recovery, audit, _ = recovery_repositories

    monkeypatch.setattr(
        "app.agent.recovery_agent.choose_recovery_action",
        lambda **_: RecommendedAction.SMART_RETRY,
    )

    result = await run_recovery_agent(
        "PAYMENT_PHASE2",
        requested_action=RecommendedAction.REMINDER,
    )

    assert result["recommended_action"] == "SMART_RETRY"
    assert result["action"] == "REMINDER"
    assert result["success"] is True
    assert result["recovery_case"]["recommended_action"] == "SMART_RETRY"
    assert result["recovery_case"]["status"] == "awaiting_customer"
    assert payment_repo.payment.status == PaymentStatus.FAILED
    assert attempts.attempts == []
    assert audit.logs[-1].action == "REMINDER"


@pytest.mark.anyio
async def test_smart_retry_creates_attempt_and_updates_payment_state(
    recovery_repositories,
    monkeypatch,
):
    payment_repo, attempts, recovery, audit, _ = recovery_repositories

    monkeypatch.setattr(
        "app.agent.recovery_agent.RecoverySimulator.simulate",
        lambda self, **_: RecoverySimulationResult(
            succeeded=True,
            recovery_probability=0.85,
            reason="Deterministic test recovery succeeded.",
        ),
    )

    result = await run_recovery_agent(
        "PAYMENT_PHASE2",
        requested_action=RecommendedAction.SMART_RETRY,
    )

    assert result["action"] == "SMART_RETRY"
    assert result["success"] is True
    assert len(attempts.attempts) == 1
    assert attempts.attempts[0].attempt_number == 1
    assert attempts.attempts[0].status == PaymentAttemptStatus.SUCCESS
    assert payment_repo.payment.status == PaymentStatus.RECOVERED
    assert recovery.case.status == RecoveryCaseStatus.RECOVERED
    assert audit.logs[-1].action == "SMART_RETRY"


@pytest.mark.anyio
async def test_max_attempt_guardrail_prevents_fourth_attempt(
    recovery_repositories,
):
    payment_repo, attempts, recovery, audit, _ = recovery_repositories

    attempts.attempts = [
        PaymentAttempt(
            payment_id=payment_repo.payment.id,
            attempt_number=index,
            status=PaymentAttemptStatus.FAILED,
            failure_reason="Previous retry failed",
            attempted_at=NOW,
        )
        for index in range(1, MAX_RECOVERY_ATTEMPTS + 1)
    ]

    recovery.case = make_case()

    result = await run_recovery_agent(
        payment_repo.payment.id,
        requested_action=RecommendedAction.SMART_RETRY,
    )

    assert result["action"] == "STOP"
    assert result["success"] is False
    assert len(attempts.attempts) == MAX_RECOVERY_ATTEMPTS
    assert audit.logs[-1].action == "STOP"


def test_recovery_action_api_returns_camel_case_and_action_metadata(
    monkeypatch,
):
    payment = make_payment()
    payment_repo = MemoryPaymentRepository(payment)

    monkeypatch.setattr(
        "app.api.recovery_cases.get_payment_repository",
        lambda: payment_repo,
    )

    async def fake_recover_payment(payment, requested_action=None):
        return {
            "success": True,
            "payment": payment.model_dump(mode="json"),
            "probability": 0.91,
            "action": "REMINDER",
            "recommended_action": "SMART_RETRY",
            "recovery_case": make_case().model_dump(mode="json"),
            "payment_attempt": None,
            "ai_explanation": {
                "probability": 0.91,
                "probabilityPercent": 91.0,
                "riskLevel": "LOW",
                "recommendedAction": "SMART_RETRY",
                "summary": "High recovery potential.",
                "reasoning": "A controlled retry is recommended.",
                "nextStep": "Perform one controlled recovery retry.",
                "paymentAmount": 1499.0,
                "paymentMethod": "UPI",
                "failureReason": "Insufficient Funds",
                "previousAttempts": 0,
                "failedAttempts": 0,
            },
        }

    monkeypatch.setattr(
        "app.api.recovery_cases.recover_payment",
        fake_recover_payment,
    )

    response = client.post(
        "/api/recovery-cases/action/PAYMENT_PHASE2",
        json={"action": "REMINDER"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["paymentId"] == "PAYMENT_PHASE2"
    assert body["requestedAction"] == "REMINDER"
    assert body["recommendedAction"] == "SMART_RETRY"
    assert body["selectedAction"] == "REMINDER"
    assert body["actionOverridden"] is True
    assert body["result"]["recommendedAction"] == "SMART_RETRY"
    assert body["result"]["recoveryCase"]["paymentId"] == "PAYMENT_PHASE2"
    assert "payment_id" not in body


def test_invalid_recovery_action_returns_422(monkeypatch):
    payment_repo = MemoryPaymentRepository(make_payment())

    monkeypatch.setattr(
        "app.api.recovery_cases.get_payment_repository",
        lambda: payment_repo,
    )

    response = client.post(
        "/api/recovery-cases/action/PAYMENT_PHASE2",
        json={"action": "NOT_A_REAL_ACTION"},
    )

    assert response.status_code == 422


def test_missing_payment_returns_404(monkeypatch):
    class EmptyPaymentRepository:
        async def find_one(self, filter_query=None):
            return None

        async def find_by_id(self, item_id):
            return None

    monkeypatch.setattr(
        "app.api.recovery_cases.get_payment_repository",
        lambda: EmptyPaymentRepository(),
    )

    response = client.post(
        "/api/recovery-cases/action/UNKNOWN",
        json={"action": "SMART_RETRY"},
    )

    assert response.status_code == 404


def test_dashboard_reflects_recovered_payment(monkeypatch):
    payment = make_payment(PaymentStatus.RECOVERED)

    customer = Customer(
        id="CUSTOMER_1",
        merchant_id="MERCHANT_1",
        name="Phase 2 Customer",
        email="phase2@example.com",
        phone="+91 90000 00001",
        risk_score=0.40,
        created_at=NOW,
    )

    attempt = PaymentAttempt(
        payment_id=payment.id,
        attempt_number=1,
        status=PaymentAttemptStatus.SUCCESS,
        attempted_at=NOW,
    )

    case = make_case(status=RecoveryCaseStatus.RECOVERED)

    monkeypatch.setattr(
        "app.api.dashboard.get_payment_repository",
        lambda: MemoryPaymentRepository(payment),
    )
    monkeypatch.setattr(
        "app.api.dashboard.get_customer_repository",
        lambda: MemoryCustomerRepository(customer),
    )
    monkeypatch.setattr(
        "app.api.dashboard.get_payment_attempt_repository",
        lambda: MemoryAttemptRepository([attempt]),
    )
    monkeypatch.setattr(
        "app.api.dashboard.get_recovery_case_repository",
        lambda: MemoryRecoveryRepository(case),
    )

    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200

    stats = response.json()["stats"]

    assert stats["successfulPayments"] == 1
    assert stats["failedPayments"] == 0
    assert stats["revenueRecovered"] == 1499.0
    assert stats["recoveryRate"] == 100.0