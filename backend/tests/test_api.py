"""API contract tests for the frontend-facing RecoverAI endpoints."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.auth import get_current_merchant
from app.models.domain import (
    AIConversation,
    Customer,
    Payment,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
    RecommendedAction,
    RecoveryCase,
    RecoveryCaseStatus,
)
from app.api.auth import get_current_merchant


client = TestClient(app)


async def fake_current_merchant():
    return type(
        "TestMerchant",
        (),
        {
            "id": "DEMO_MERCHANT_1",
        },
    )()


app.dependency_overrides[get_current_merchant] = fake_current_merchant

NOW = datetime.now(timezone.utc)


class FakePaymentRepository:
    def __init__(self):
        self.payment = Payment(
            id="DEMO_PAYMENT_1",
            merchant_id="DEMO_MERCHANT_1",
            customer_id="DEMO_CUSTOMER_1",
            amount=1499,
            currency="INR",
            status=PaymentStatus.FAILED,
            payment_method="UPI",
            failure_reason="Insufficient Funds",
            created_at=NOW,
        )

    async def find_many(self, filter_query=None, limit=100):
        """
        Mimic the real repository's filtered find_many() behavior.

        Supports:
        - merchant_id filtering
        - payment id filtering
        - customer_id filtering
        """

        if not filter_query:
            return [self.payment][:limit]

        if (
            "id" in filter_query
            and filter_query["id"] != self.payment.id
        ):
            return []

        if (
            "merchant_id" in filter_query
            and str(filter_query["merchant_id"])
            != str(self.payment.merchant_id)
        ):
            return []

        if (
            "customer_id" in filter_query
            and filter_query["customer_id"]
            != self.payment.customer_id
        ):
            return []

        return [self.payment][:limit]

    async def find_by_id(self, item_id):
        return (
            self.payment
            if item_id == self.payment.id
            else None
        )

    async def find_one(self, filter_query=None):
        if not filter_query:
            return self.payment

        if (
            "id" in filter_query
            and filter_query["id"] != self.payment.id
        ):
            return None

        if (
            "merchant_id" in filter_query
            and str(filter_query["merchant_id"])
            != str(self.payment.merchant_id)
        ):
            return None

        if (
            "customer_id" in filter_query
            and filter_query["customer_id"]
            != self.payment.customer_id
        ):
            return None

        return self.payment


class FakeCustomerRepository:
    def __init__(self):
        self.customer = Customer(
            id="DEMO_CUSTOMER_1",
            merchant_id="DEMO_MERCHANT_1",
            name="Demo Customer",
            email="demo.customer@recoverai.com",
            phone="+919999999999",
            risk_score=0.45,
        )

    async def find_many(self, filter_query=None, limit=100):
        if not filter_query:
            return [self.customer][:limit]

        if (
            "id" in filter_query
            and filter_query["id"] != self.customer.id
        ):
            return []

        if (
            "merchant_id" in filter_query
            and str(filter_query["merchant_id"])
            != str(self.customer.merchant_id)
        ):
            return []

        return [self.customer][:limit]

    async def find_by_id(self, item_id):
        return (
            self.customer
            if item_id == self.customer.id
            else None
        )

    async def find_one(self, filter_query=None):
        if not filter_query:
            return self.customer

        if (
            "id" in filter_query
            and filter_query["id"] != self.customer.id
        ):
            return None

        if (
            "merchant_id" in filter_query
            and str(filter_query["merchant_id"])
            != str(self.customer.merchant_id)
        ):
            return None

        return self.customer


class FakeAttemptRepository:
    def __init__(self):
        self.attempt = PaymentAttempt(
            id="ATTEMPT_1",
            payment_id="DEMO_PAYMENT_1",
            attempt_number=1,
            status=PaymentAttemptStatus.FAILED,
            failure_reason="Insufficient Funds",
            attempted_at=NOW,
        )

    async def find_many(self, filter_query=None, limit=100):
        if (
            filter_query
            and filter_query.get("payment_id")
            != self.attempt.payment_id
        ):
            return []

        return [self.attempt][:limit]

    async def count(self, filter_query=None):
        return len(
            await self.find_many(filter_query)
        )


class FakeRecoveryRepository:
    def __init__(self):
        self.case = RecoveryCase(
            id="DEMO_RECOVERY_CASE_1",
            payment_id="DEMO_PAYMENT_1",
            customer_id="DEMO_CUSTOMER_1",
            recovery_probability=0.91,
            status=RecoveryCaseStatus.PENDING,
            recommended_action=RecommendedAction.SMART_RETRY,
            created_at=NOW,
            updated_at=NOW,
        )

    async def find_many(self, filter_query=None, limit=100):
        if (
            filter_query
            and filter_query.get("payment_id")
            not in (None, self.case.payment_id)
        ):
            return []

        if filter_query and "customer_id" in filter_query:
            if (
                filter_query["customer_id"]
                != self.case.customer_id
            ):
                return []

        if filter_query and "status" in filter_query:
            allowed = filter_query["status"].get(
                "$in",
                [],
            )

            if self.case.status.value not in allowed:
                return []

        return [self.case][:limit]

    async def find_by_id(self, item_id):
        return (
            self.case
            if item_id == self.case.id
            else None
        )

    async def find_one(self, filter_query=None):
        if not filter_query:
            return self.case

        if (
            "payment_id" in filter_query
            and filter_query["payment_id"]
            != self.case.payment_id
        ):
            return None

        if (
            "customer_id" in filter_query
            and filter_query["customer_id"]
            != self.case.customer_id
        ):
            return None

        return self.case


class FakeConversationRepository:
    def __init__(self):
        self.conversation = None

    async def find_by_id(self, item_id):
        return (
            self.conversation
            if self.conversation
            and self.conversation.id == item_id
            else None
        )

    async def insert(self, item):
        self.conversation = item
        return item

    async def update_by_id(self, item_id, updates):
        if (
            not self.conversation
            or self.conversation.id != item_id
        ):
            return None

        for key, value in updates.items():
            if key == "messages":
                continue

            setattr(
                self.conversation,
                key,
                value,
            )

        return self.conversation


@pytest.fixture
def patch_repositories(monkeypatch):
    payment = FakePaymentRepository()
    customer = FakeCustomerRepository()
    attempts = FakeAttemptRepository()
    recovery = FakeRecoveryRepository()

    monkeypatch.setattr(
        "app.api.payments.get_payment_repository",
        lambda: payment,
    )
    monkeypatch.setattr(
        "app.api.payments.get_customer_repository",
        lambda: customer,
    )
    monkeypatch.setattr(
        "app.api.payments.get_payment_attempt_repository",
        lambda: attempts,
    )
    monkeypatch.setattr(
        "app.api.payments.get_recovery_case_repository",
        lambda: recovery,
    )

    monkeypatch.setattr(
        "app.api.customers.get_customer_repository",
        lambda: customer,
    )
    monkeypatch.setattr(
        "app.api.customers.get_payment_repository",
        lambda: payment,
    )
    monkeypatch.setattr(
        "app.api.customers.get_recovery_case_repository",
        lambda: recovery,
    )

    monkeypatch.setattr(
        "app.api.recovery_cases.get_recovery_case_repository",
        lambda: recovery,
    )
    monkeypatch.setattr(
        "app.api.recovery_cases.get_payment_repository",
        lambda: payment,
    )
    monkeypatch.setattr(
        "app.api.recovery_cases.get_customer_repository",
        lambda: customer,
    )
    monkeypatch.setattr(
        "app.api.recovery_cases.get_payment_attempt_repository",
        lambda: attempts,
    )

    monkeypatch.setattr(
        "app.services.api_dto.predict_recovery_probability",
        lambda _: 0.91,
    )
    
    app.dependency_overrides[get_current_merchant] = fake_current_merchant

    return (
        payment,
        customer,
        attempts,
        recovery,
    )


def test_list_payments_returns_canonical_dto(
    patch_repositories,
):
    response = client.get("/api/payments")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1

    payment = body[0]

    assert payment["customerId"] == "DEMO_CUSTOMER_1"
    assert payment["customerName"] == "Demo Customer"
    assert (
        payment["customerEmail"]
        == "demo.customer@recoverai.com"
    )
    assert payment["paymentMethod"] == "UPI"
    assert (
        payment["failureReason"]
        == "Insufficient Funds"
    )
    assert payment["recoveryProbability"] == 91.0
    assert (
        payment["recommendedAction"]
        == "SMART_RETRY"
    )
    assert (
        payment["attempts"][0]["attemptNumber"]
        == 1
    )
    assert (
        payment["attempts"][0]["paymentId"]
        == "DEMO_PAYMENT_1"
    )
    assert "customer_id" not in payment


def test_get_payment_details_is_complete(
    patch_repositories,
):
    response = client.get(
        "/api/payments/DEMO_PAYMENT_1"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["customerName"] == "Demo Customer"
    assert body["amount"] == 1499.0
    assert body["recoveryProbability"] == 91.0
    assert (
        body["recommendedAction"]
        == "SMART_RETRY"
    )
    assert len(body["attempts"]) == 1
    assert body["timeline"]
    assert (
        body["aiExplanation"]["recommendedAction"]
        == "SMART_RETRY"
    )
    assert (
        body["aiExplanation"]["probabilityPercent"]
        == 91.0
    )


def test_get_unknown_payment_returns_404(
    patch_repositories,
):
    response = client.get(
        "/api/payments/UNKNOWN_PAYMENT"
    )

    assert response.status_code == 404


def test_customers_returns_aggregated_canonical_dto(
    patch_repositories,
):
    response = client.get("/api/customers")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1

    customer = body[0]

    assert customer["totalPayments"] == 1
    assert customer["failedPayments"] == 1
    assert customer["successfulPayments"] == 0
    assert customer["totalAmount"] == 1499.0
    assert customer["riskProfile"] == "Medium Risk"


def test_recovery_cases_returns_canonical_dto(
    patch_repositories,
):
    response = client.get("/api/recovery-cases")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1

    case = body[0]

    assert case["paymentId"] == "DEMO_PAYMENT_1"
    assert case["customerName"] == "Demo Customer"
    assert case["recoveryProbability"] == 91.0
    assert (
        case["recommendedAction"]
        == "SMART_RETRY"
    )
    assert case["attempts"] == 1
    assert (
        case["aiExplanation"]["probabilityPercent"]
        == 91.0
    )


def test_dashboard_contract(
    patch_repositories,
    monkeypatch,
):
    (
        payment,
        customer,
        attempts,
        recovery,
    ) = patch_repositories

    monkeypatch.setattr(
        "app.api.dashboard.get_payment_repository",
        lambda: payment,
    )
    monkeypatch.setattr(
        "app.api.dashboard.get_customer_repository",
        lambda: customer,
    )
    monkeypatch.setattr(
        "app.api.dashboard.get_payment_attempt_repository",
        lambda: attempts,
    )
    monkeypatch.setattr(
        "app.api.dashboard.get_recovery_case_repository",
        lambda: recovery,
    )

    response = client.get(
        "/api/dashboard/stats"
    )

    assert response.status_code == 200

    body = response.json()

    assert set(body) == {
        "stats",
        "revenueChart",
        "statusChart",
        "recentAttempts",
        "topFailureReasons",
        "recommendations",
    }

    assert (
        body["stats"]["totalTransactions"]
        == 1
    )

    assert (
        body["recentAttempts"][0]["action"]
        == "SMART_RETRY"
    )


def test_analytics_contract_and_attempt_enrichment(
    patch_repositories,
    monkeypatch,
):
    (
        payment,
        customer,
        attempts,
        recovery,
    ) = patch_repositories

    monkeypatch.setattr(
        "app.api.analytics.get_payment_repository",
        lambda: payment,
    )
    monkeypatch.setattr(
        "app.api.analytics.get_payment_attempt_repository",
        lambda: attempts,
    )
    monkeypatch.setattr(
        "app.api.analytics.get_recovery_case_repository",
        lambda: recovery,
    )

    response = client.get("/api/analytics")

    assert response.status_code == 200

    body = response.json()

    assert set(body) == {
        "revenueAtRisk",
        "revenueRecovered",
        "recoveryRate",
        "recoveryAttempts",
        "successfulRecoveries",
        "recoveryByMethod",
        "recoveryByReason",
        "performanceOverTime",
    }

    assert (
        body["recoveryByMethod"][0]["method"]
        == "UPI"
    )

    assert (
        body["recoveryByMethod"][0]["attempted"]
        == 1499.0
    )


def test_ai_response_uses_camel_case_contract(
    monkeypatch,
):
    conversations = FakeConversationRepository()

    monkeypatch.setattr(
        "app.api.ai.get_ai_conversation_repository",
        lambda: conversations,
    )

    response = client.post(
        "/api/ai/message",
        json={
            "message": "What does RecoverAI do?",
            "history": [],
            "merchant_id": "test-merchant-1",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["type"] == "general"
    assert body["reply"]
    assert body["conversationId"]
    assert "conversation_id" not in body


def test_recovery_action_returns_updated_public_dtos(
    patch_repositories,
    monkeypatch,
):
    (
        payment,
        customer,
        attempts,
        recovery,
    ) = patch_repositories

    async def fake_recover(
        payment,
        requested_action=None,
    ):
        assert (
            requested_action
            == RecommendedAction.SMART_RETRY
        )

        return {
            "payment": payment.model_dump(
                mode="json"
            ),
            "recovery_case": recovery.case.model_dump(
                mode="json"
            ),
            "payment_attempt": {
                "id": "ATTEMPT_2",
                "payment_id": payment.id,
                "attempt_number": 2,
                "status": "success",
                "attempted_at": NOW.isoformat(),
            },
            "audit_log": {
                "id": "AUDIT_2",
                "payment_id": payment.id,
                "action": "SMART_RETRY",
                "reason": "Recovery succeeded.",
                "confidence": 0.91,
                "created_at": NOW.isoformat(),
            },
            "probability": 0.91,
            "action": "SMART_RETRY",
            "success": True,
            "ai_explanation": {
                "probability": 0.91,
                "probabilityPercent": 91.0,
                "riskLevel": "Low Risk",
                "recommendedAction": "SMART_RETRY",
                "summary": (
                    "Retry is likely to recover "
                    "the payment."
                ),
                "reasoning": (
                    "The payment has a high "
                    "recovery probability."
                ),
                "nextStep": "Retry the payment.",
                "paymentAmount": 1499.0,
                "paymentMethod": "UPI",
                "failureReason": "Insufficient Funds",
                "previousAttempts": 1,
                "failedAttempts": 1,
            },
        }

    monkeypatch.setattr(
        "app.api.recovery_cases.recover_payment",
        fake_recover,
    )

    response = client.post(
        "/api/recovery-cases/action/"
        "DEMO_PAYMENT_1",
        json={
            "action": "SMART_RETRY",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["paymentId"]
        == "DEMO_PAYMENT_1"
    )
    assert (
        body["requestedAction"]
        == "SMART_RETRY"
    )
    assert (
        body["selectedAction"]
        == "SMART_RETRY"
    )
    assert (
        body["actionOverridden"]
        is False
    )

    assert (
        body["result"]["payment"]["customerId"]
        == "DEMO_CUSTOMER_1"
    )

    assert (
        body["result"]["recoveryCase"]["paymentId"]
        == "DEMO_PAYMENT_1"
    )

    assert (
        body["result"]["paymentAttempt"]["paymentId"]
        == "DEMO_PAYMENT_1"
    )

    assert (
        body["result"]["paymentAttempt"][
            "attemptNumber"
        ]
        == 2
    )

    assert (
        "payment_id"
        not in body["result"]["payment"]
    )

    assert (
        "payment_id"
        not in body["result"]["paymentAttempt"]
    )


def test_recovery_action_rejects_invalid_action(
    patch_repositories,
):
    response = client.post(
        "/api/recovery-cases/action/"
        "DEMO_PAYMENT_1",
        json={
            "action": "NOT_A_REAL_ACTION",
        },
    )

    assert response.status_code == 422


def test_recovery_action_unknown_payment_returns_404(
    patch_repositories,
):
    response = client.post(
        "/api/recovery-cases/action/"
        "UNKNOWN_PAYMENT",
        json={
            "action": "SMART_RETRY",
        },
    )

    assert response.status_code == 404