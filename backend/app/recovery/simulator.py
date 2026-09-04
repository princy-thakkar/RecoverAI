from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class RecoverySimulationResult:
    succeeded: bool
    recovery_probability: float
    reason: str


class RecoverySimulator:
    """
    Independent synthetic recovery outcome simulator.

    IMPORTANT:
    The ML model's predicted probability is NOT used to decide
    whether the payment succeeds.

    The simulator represents hidden ground truth for benchmarking.
    It is deterministic so benchmark results are reproducible.

    This is NOT a production payment processor.
    """

    def simulate(
        self,
        *,
        payment_id: str,
        amount: float,
        failure_reason: str | None,
        action: str,
        attempt_number: int,
    ) -> RecoverySimulationResult:
        propensity = self._hidden_recovery_propensity(
            payment_id=payment_id,
            amount=amount,
            failure_reason=failure_reason,
            action=action,
            attempt_number=attempt_number,
        )

        random_value = self._stable_random_value(
            payment_id=payment_id,
            attempt_number=attempt_number,
            action=action,
        )

        succeeded = random_value < propensity

        if succeeded:
            reason = (
                f"Independent recovery simulation succeeded for "
                f"{action}. Hidden outcome propensity was "
                f"{propensity:.2%}."
            )
        else:
            reason = (
                f"Independent recovery simulation failed for "
                f"{action}. Hidden outcome propensity was "
                f"{propensity:.2%}."
            )

        return RecoverySimulationResult(
            succeeded=succeeded,
            recovery_probability=propensity,
            reason=reason,
        )

    @staticmethod
    def _hidden_recovery_propensity(
        *,
        payment_id: str,
        amount: float,
        failure_reason: str | None,
        action: str,
        attempt_number: int,
    ) -> float:
        """
        Hidden ground-truth propensity.

        The important design choice is that retryable failures have
        materially higher recovery propensity than non-retryable
        failures.

        The ML prediction is NOT consulted here.
        """

        reason = (failure_reason or "").lower()

        # Base propensity for a failed payment.
        propensity = 0.20

        # Failure-type signal.
        if "insufficient" in reason:
            # Customer may retry after balance changes.
            propensity += 0.45

        elif "network" in reason or "timeout" in reason:
            # Transient infrastructure failures are highly retryable.
            propensity += 0.40

        elif "expired" in reason:
            # Updating payment method is preferable to blind retry.
            propensity += 0.02

        elif "invalid" in reason:
            # Invalid payment details should not be blindly retried.
            propensity -= 0.05

        elif "fraud" in reason or "blocked" in reason:
            # Strongly non-retryable.
            propensity -= 0.15

        # Action effectiveness.
        if action == "SMART_RETRY":
            propensity += 0.20

        elif action == "PAYMENT_METHOD_SUGGESTION":
            propensity += 0.18

        elif action == "REMINDER":
            propensity += 0.08

        elif action == "SUPPORT_ESCALATION":
            propensity += 0.05

        # Repeated attempts become less effective.
        if attempt_number >= 2:
            propensity -= 0.10

        if attempt_number >= 3:
            propensity -= 0.15

        return max(0.02, min(0.95, propensity))

    @staticmethod
    def _stable_random_value(
        *,
        payment_id: str,
        attempt_number: int,
        action: str,
    ) -> float:
        seed = (
            f"{payment_id}:"
            f"{attempt_number}:"
            f"{action}"
        )

        digest = hashlib.sha256(
            seed.encode("utf-8")
        ).hexdigest()

        integer = int(digest[:16], 16)

        return integer / float(16**16 - 1)