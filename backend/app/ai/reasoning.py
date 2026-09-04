from __future__ import annotations

from typing import Any


def analyze_recovery_decision(
    payment: dict[str, Any],
    probability: float,
    recommended_action: str,
) -> dict[str, Any]:
    """
    Generate a clear, human-readable explanation for a
    RecoverAI recovery recommendation.

    This layer does NOT make the ML decision.
    It explains the probability and action produced by
    the prediction and decision layers.
    """

    amount = float(payment.get("amount", 0))

    payment_method = str(
        payment.get("payment_method", "Unknown")
    ).replace("_", " ").upper()

    failure_reason = str(
        payment.get("failure_reason", "Unknown failure")
    )

    previous_attempts = int(
        payment.get("previous_attempts", 0)
    )

    failed_attempts = int(
        payment.get("failed_attempts", 0)
    )

    probability_percent = probability * 100

    # =========================================================
    # RISK CLASSIFICATION
    # =========================================================

    if probability >= 0.80:
        risk_level = "LOW"
    elif probability >= 0.50:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # =========================================================
    # PAYMENT CONTEXT
    # =========================================================

    if previous_attempts == 0:
        attempt_summary = (
            "No previous recovery attempts have been made."
        )
    elif previous_attempts == 1:
        attempt_summary = (
            "One previous recovery attempt has been made."
        )
    else:
        attempt_summary = (
            f"{previous_attempts} previous recovery attempts "
            "have been made."
        )

    if failed_attempts == 0:
        failure_attempt_summary = (
            "There are no previously failed recovery attempts."
        )
    elif failed_attempts == 1:
        failure_attempt_summary = (
            "One previous recovery attempt failed."
        )
    else:
        failure_attempt_summary = (
            f"{failed_attempts} previous recovery attempts failed."
        )

    # =========================================================
    # RECOMMENDED NEXT STEP
    # =========================================================

    if recommended_action == "SMART_RETRY":

        next_step = (
            "Perform one controlled recovery retry and monitor "
            "the outcome."
        )

        action_explanation = (
            "The payment has a strong predicted recovery probability "
            "and has not exceeded the automated retry limit."
        )

    elif recommended_action == "REMINDER":

        next_step = (
            "Notify the customer and allow them to resolve the "
            "payment issue before attempting another recovery."
        )

        action_explanation = (
            "A customer reminder is safer than immediately "
            "performing another automated retry."
        )

    elif recommended_action == "PAYMENT_METHOD_SUGGESTION":

        next_step = (
            "Suggest an alternative payment method to the customer."
        )

        action_explanation = (
            "Changing the payment method may provide a better "
            "recovery opportunity than another attempt."
        )

    elif recommended_action == "SUPPORT_ESCALATION":

        next_step = (
            "Escalate the payment to support for manual review."
        )

        action_explanation = (
            "The payment should receive manual attention rather "
            "than continuing automated recovery attempts."
        )

    elif recommended_action == "STOP":

        if previous_attempts >= 3:

            next_step = (
                "Do not perform another automated retry. "
                "The payment has reached the recovery attempt limit."
            )

            action_explanation = (
                "Continuing automated retries could create unnecessary "
                "customer friction or repeated failures."
            )

        else:

            next_step = (
                "Stop automated recovery attempts and review "
                "the payment manually."
            )

            action_explanation = (
                "The current recovery probability is too low to "
                "justify another automated attempt."
            )

    else:

        next_step = (
            "Review the payment manually before taking further action."
        )

        action_explanation = (
            "The current conditions do not match a predefined "
            "automated recovery strategy."
        )

    # =========================================================
    # HUMAN-READABLE REASONING
    # =========================================================

    reasoning = (
        f"RecoverAI recommends {recommended_action} for this payment. "
        f"The {payment_method} payment failed because of "
        f"{failure_reason}. "
        f"RecoverAI estimates a {probability_percent:.2f}% "
        f"probability of successful recovery, which places this "
        f"payment in the {risk_level} recovery-risk category. "
        f"{attempt_summary} "
        f"{failure_attempt_summary} "
        f"The transaction amount is ₹{amount:,.2f}. "
        f"{action_explanation}"
    )

    # =========================================================
    # SHORT SUMMARY
    # =========================================================

    if recommended_action == "SMART_RETRY":
        summary = (
            f"High recovery potential ({probability_percent:.2f}%). "
            f"One controlled retry is recommended."
        )

    elif recommended_action == "REMINDER":
        summary = (
            f"Moderate recovery potential ({probability_percent:.2f}%). "
            f"Customer action is recommended before another retry."
        )

    elif recommended_action == "PAYMENT_METHOD_SUGGESTION":
        summary = (
            f"Recovery probability is {probability_percent:.2f}%. "
            f"An alternative payment method is recommended."
        )

    elif recommended_action == "SUPPORT_ESCALATION":
        summary = (
            f"Recovery probability is {probability_percent:.2f}%. "
            f"Manual support intervention is recommended."
        )

    elif recommended_action == "STOP":
        summary = (
            f"Low recovery potential ({probability_percent:.2f}%). "
            f"Automated recovery should stop."
        )

    else:
        summary = (
            f"Recovery probability is {probability_percent:.2f}%. "
            f"Manual review is recommended."
        )

    return {
        "probability": round(probability, 4),
        "probability_percent": round(probability_percent, 2),
        "risk_level": risk_level,
        "recommended_action": recommended_action,
        "summary": summary,
        "reasoning": reasoning,
        "next_step": next_step,
        "payment_amount": round(amount, 2),
        "payment_method": payment_method,
        "failure_reason": failure_reason,
        "previous_attempts": previous_attempts,
        "failed_attempts": failed_attempts,
    }
