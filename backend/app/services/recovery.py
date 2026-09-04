from __future__ import annotations

from typing import Any

from app.agent.recovery_agent import run_recovery_agent
from app.models.domain import Payment, RecommendedAction


async def recover_payment(
    payment: Payment,
    requested_action: RecommendedAction | None = None,
) -> dict[str, Any]:
    """
    Run the complete RecoverAI recovery workflow.

    The recovery agent is responsible for:

        Payment
            ↓
        Previous attempts
            ↓
        ML prediction
            ↓
        Recovery decision
            ↓
        Guardrails
            ↓
        Recovery action
            ↓
        Payment simulation
            ↓
        Database updates
            ↓
        Audit log
            ↓
        AI explanation

    This service layer provides a clean interface between
    the API and the recovery agent.
    """

    result = await run_recovery_agent(
        payment.id,
        requested_action=requested_action,
    )

    if result is None:
        return {
            "success": False,
            "message": "Payment not found.",
        }

    return {
        "success": bool(result.get("success")),
        **result,
    }