from __future__ import annotations

from typing import Any


FAILURE_REASON_CODES = {
    "insufficient funds": 1.0,
    "bank declined": 2.0,

    "timeout": 3.0,
    "network timeout": 3.0,
    "payment gateway timeout": 3.0,
    "gateway timeout": 3.0,

    "network error": 4.0,

    "expired card": 5.0,
    "card expired": 5.0,

    "invalid card": 6.0,
    "fraud suspected": 7.0,
    "account blocked": 8.0,
}


def build_features(payment: dict[str, Any]) -> list[float]:
    """
    Convert payment information into numerical features.

    Feature order:

    1. amount
    2. previous_attempts
    3. failed_attempts
    4. amount_is_high
    5. is_upi
    6. is_card
    7. is_net_banking
    8. failure_reason_code
    """

    amount = float(
        payment.get("amount", 0)
    )

    previous_attempts = int(
        payment.get("previous_attempts", 0)
    )

    failed_attempts = int(
        payment.get("failed_attempts", 0)
    )

    payment_method = str(
        payment.get("payment_method", "")
    ).strip().lower()

    failure_reason = str(
        payment.get("failure_reason", "")
    ).strip().lower()

    amount_is_high = (
        1.0
        if amount >= 1000
        else 0.0
    )

    is_upi = (
        1.0
        if payment_method == "upi"
        else 0.0
    )

    is_card = (
        1.0
        if payment_method == "card"
        else 0.0
    )

    is_net_banking = (
        1.0
        if payment_method in {
            "net banking",
            "net_banking",
        }
        else 0.0
    )

    failure_reason_code = FAILURE_REASON_CODES.get(
        failure_reason,
        0.0,
    )

    return [
        amount,
        float(previous_attempts),
        float(failed_attempts),
        amount_is_high,
        is_upi,
        is_card,
        is_net_banking,
        failure_reason_code,
    ]
    
