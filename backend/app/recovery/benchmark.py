from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from enum import Enum

from app.agent.decision import choose_recovery_action
from app.ml.predict import predict_recovery_probability
from app.models.domain import RecommendedAction
from app.policy.engine import evaluate_recovery_action
from app.recovery.simulator import RecoverySimulator


class BenchmarkStrategy(str, Enum):
    NEVER_RETRY = "NEVER_RETRY"
    RETRY_ALL_ONCE = "RETRY_ALL_ONCE"
    RECOVERAI = "RECOVERAI"


@dataclass
class BenchmarkPayment:
    payment_id: str
    amount: float
    failure_reason: str
    payment_method: str


@dataclass
class BenchmarkResult:
    strategy: str
    batch_size: int
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float
    successful_recoveries: int

    automated_actions: int
    customer_actions: int
    escalations: int
    total_interventions: int

    stopped: int
    attempts: int
    unsafe_actions_blocked: int

    automated_attempts_per_successful_recovery: float
    interventions_per_successful_recovery: float
    revenue_recovered_per_automated_attempt: float
    attempt_reduction_vs_retry_all_pct: float

    def to_dict(self) -> dict:
        return asdict(self)


class RecoveryBenchmark:
    """
    Synthetic batch benchmark for RecoverAI.

    RecoverAI strategy:

        payment
          -> actual ML predictor
          -> actual decision engine
          -> actual policy engine
          -> independent recovery simulator

    Baselines:

        NEVER_RETRY
        RETRY_ALL_ONCE

    IMPORTANT:

    The ML prediction is NEVER used as payment ground truth.

    The independent RecoverySimulator provides the hidden outcome.

    This benchmark is synthetic and deterministic. It does not
    represent production payment-processing performance.
    """

    def __init__(self) -> None:
        self.simulator = RecoverySimulator()

    def run(
        self,
        batch_size: int = 250,
        seed: int = 2026,
    ) -> dict:
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")

        payments = self._generate_cohort(
            batch_size=batch_size,
            seed=seed,
        )

        retry_all = self._run_retry_all_once(payments)

        results = [
            self._run_never_retry(payments),
            retry_all,
            self._run_recoverai(
                payments,
                retry_all=retry_all,
            ),
        ]

        return {
            "synthetic": True,
            "seed": seed,
            "batch_size": batch_size,
            "ground_truth": (
                "Independent deterministic RecoverySimulator"
            ),
            "recoverai_pipeline": (
                "ML predictor -> decision engine -> policy engine"
            ),
            "strategies": [
                result.to_dict()
                for result in results
            ],
        }

    # =========================================================
    # Cohort generation
    # =========================================================

    def _generate_cohort(
        self,
        *,
        batch_size: int,
        seed: int,
    ) -> list[BenchmarkPayment]:
        rng = random.Random(seed)

        failure_reasons = [
            "Insufficient Funds",
            "Timeout",
            "Network Error",
            "Expired Card",
            "Invalid Card",
            "Bank Declined",
        ]

        payment_methods = [
            "UPI",
            "CARD",
            "NET_BANKING",
        ]

        payments: list[BenchmarkPayment] = []

        for index in range(batch_size):
            amount = round(
                rng.uniform(100, 5000),
                2,
            )

            failure_reason = rng.choice(
                failure_reasons
            )

            payment_method = rng.choice(
                payment_methods
            )

            payments.append(
                BenchmarkPayment(
                    payment_id=(
                        f"BENCH_{seed}_{index:04d}"
                    ),
                    amount=amount,
                    failure_reason=failure_reason,
                    payment_method=payment_method,
                )
            )

        return payments

    # =========================================================
    # Baseline: never retry
    # =========================================================

    def _run_never_retry(
        self,
        payments: list[BenchmarkPayment],
    ) -> BenchmarkResult:
        revenue_at_risk = sum(
            payment.amount
            for payment in payments
        )

        return BenchmarkResult(
            strategy=BenchmarkStrategy.NEVER_RETRY.value,
            batch_size=len(payments),
            revenue_at_risk=round(
                revenue_at_risk,
                2,
            ),
            revenue_recovered=0.0,
            recovery_rate=0.0,
            successful_recoveries=0,

            automated_actions=0,
            customer_actions=0,
            escalations=0,
            total_interventions=0,

            stopped=len(payments),
            attempts=0,
            unsafe_actions_blocked=0,

            automated_attempts_per_successful_recovery=0.0,
            interventions_per_successful_recovery=0.0,
            revenue_recovered_per_automated_attempt=0.0,
            attempt_reduction_vs_retry_all_pct=100.0,
        )

    # =========================================================
    # Baseline: retry everything once
    # =========================================================

    def _run_retry_all_once(
        self,
        payments: list[BenchmarkPayment],
    ) -> BenchmarkResult:
        revenue_at_risk = sum(
            payment.amount
            for payment in payments
        )

        recovered = 0.0
        successful = 0

        for payment in payments:
            outcome = self.simulator.simulate(
                payment_id=payment.payment_id,
                amount=payment.amount,
                failure_reason=payment.failure_reason,
                action=RecommendedAction.SMART_RETRY.value,
                attempt_number=1,
            )

            if outcome.succeeded:
                recovered += payment.amount
                successful += 1

        attempts = len(payments)

        return BenchmarkResult(
            strategy=(
                BenchmarkStrategy.RETRY_ALL_ONCE.value
            ),
            batch_size=len(payments),
            revenue_at_risk=round(
                revenue_at_risk,
                2,
            ),
            revenue_recovered=round(
                recovered,
                2,
            ),
            recovery_rate=round(
                successful / len(payments),
                4,
            ),
            successful_recoveries=successful,

            automated_actions=len(payments),
            customer_actions=0,
            escalations=0,
            total_interventions=attempts,

            stopped=0,
            attempts=attempts,
            unsafe_actions_blocked=0,

            automated_attempts_per_successful_recovery=round(
                attempts / successful,
                2,
            ) if successful else 0.0,

            interventions_per_successful_recovery=round(
                attempts / successful,
                2,
            ) if successful else 0.0,

            revenue_recovered_per_automated_attempt=round(
                recovered / attempts,
                2,
            ) if attempts else 0.0,

            attempt_reduction_vs_retry_all_pct=0.0,
        )

    # =========================================================
    # RecoverAI actual pipeline
    # =========================================================

    def _run_recoverai(
        self,
        payments: list[BenchmarkPayment],
        *,
        retry_all: BenchmarkResult,
    ) -> BenchmarkResult:
        revenue_at_risk = sum(
            payment.amount
            for payment in payments
        )

        recovered = 0.0
        successful = 0

        automated_actions = 0
        customer_actions = 0
        escalations = 0
        stopped = 0
        attempts = 0
        unsafe_actions_blocked = 0

        for payment in payments:

            # -------------------------------------------------
            # 1. Build the same feature shape used by the agent.
            # -------------------------------------------------

            payment_data = {
                "id": payment.payment_id,
                "amount": payment.amount,
                "currency": "INR",
                "status": "failed",
                "payment_method": payment.payment_method,
                "failure_reason": payment.failure_reason,
                "previous_attempts": 0,
                "failed_attempts": 0,
            }

            # -------------------------------------------------
            # 2. ACTUAL ML PREDICTOR
            # -------------------------------------------------

            probability = predict_recovery_probability(
                payment_data
            )

            # -------------------------------------------------
            # 3. ACTUAL DECISION ENGINE
            # -------------------------------------------------

            recommended_action = choose_recovery_action(
                probability=probability,
                failure_reason=payment.failure_reason,
                attempts=0,
            )

            # -------------------------------------------------
            # 4. ACTUAL POLICY ENGINE
            #
            # No merchant override is supplied in the benchmark.
            # The policy evaluates the model's recommendation.
            # -------------------------------------------------

            policy_decision = evaluate_recovery_action(
                recommended_action=recommended_action,
                requested_action=None,
                probability=probability,
                failure_reason=payment.failure_reason,
                attempts=0,
                amount=float(payment.amount),
            )

            action = policy_decision.selected_action

            # -------------------------------------------------
            # 5. Policy-blocked action
            # -------------------------------------------------

            if not policy_decision.allowed:
                unsafe_actions_blocked += 1
                stopped += 1
                continue

            # -------------------------------------------------
            # 6. Explicit STOP
            # -------------------------------------------------

            if action == RecommendedAction.STOP:
                stopped += 1
                continue

            # -------------------------------------------------
            # 7. Customer-driven / assisted interventions
            # -------------------------------------------------

            if action in {
                RecommendedAction.REMINDER,
                RecommendedAction.PAYMENT_METHOD_SUGGESTION,
                RecommendedAction.SUPPORT_ESCALATION,
            }:
                outcome = self.simulator.simulate(
                    payment_id=payment.payment_id,
                    amount=payment.amount,
                    failure_reason=payment.failure_reason,
                    action=action.value,
                    attempt_number=1,
                )

                if action in {
                    RecommendedAction.REMINDER,
                    RecommendedAction.PAYMENT_METHOD_SUGGESTION,
                }:
                    customer_actions += 1
                else:
                    escalations += 1

                if outcome.succeeded:
                    successful += 1
                    recovered += payment.amount

                continue

            # -------------------------------------------------
            # 8. Unknown action fails closed.
            # -------------------------------------------------

            if action != RecommendedAction.SMART_RETRY:
                stopped += 1
                continue

            # -------------------------------------------------
            # 9. Automated recovery attempt
            # -------------------------------------------------

            automated_actions += 1
            attempts += 1

            outcome = self.simulator.simulate(
                payment_id=payment.payment_id,
                amount=payment.amount,
                failure_reason=payment.failure_reason,
                action=action.value,
                attempt_number=1,
            )

            if outcome.succeeded:
                successful += 1
                recovered += payment.amount
            else:
                # Failed automated recovery is escalated.
                escalations += 1

        # =====================================================
        # Final metrics
        # =====================================================

        total_interventions = (
            automated_actions
            + customer_actions
            + escalations
        )

        automated_attempts_per_successful_recovery = (
            attempts / successful
            if successful
            else 0.0
        )

        interventions_per_successful_recovery = (
            total_interventions / successful
            if successful
            else 0.0
        )

        revenue_per_automated_attempt = (
            recovered / attempts
            if attempts
            else 0.0
        )

        attempt_reduction = (
            (
                1
                - (
                    attempts
                    / retry_all.attempts
                )
            )
            * 100
            if retry_all.attempts
            else 0.0
        )

        return BenchmarkResult(
            strategy=BenchmarkStrategy.RECOVERAI.value,
            batch_size=len(payments),

            revenue_at_risk=round(
                revenue_at_risk,
                2,
            ),

            revenue_recovered=round(
                recovered,
                2,
            ),

            recovery_rate=round(
                successful / len(payments),
                4,
            ),

            successful_recoveries=successful,

            automated_actions=automated_actions,
            customer_actions=customer_actions,
            escalations=escalations,
            total_interventions=total_interventions,

            stopped=stopped,
            attempts=attempts,
            unsafe_actions_blocked=unsafe_actions_blocked,

            automated_attempts_per_successful_recovery=round(
                automated_attempts_per_successful_recovery,
                2,
            ),

            interventions_per_successful_recovery=round(
                interventions_per_successful_recovery,
                2,
            ),

            revenue_recovered_per_automated_attempt=round(
                revenue_per_automated_attempt,
                2,
            ),

            attempt_reduction_vs_retry_all_pct=round(
                attempt_reduction,
                2,
            ),
        )