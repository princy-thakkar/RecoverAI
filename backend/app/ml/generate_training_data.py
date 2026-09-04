import random
from pathlib import Path

import pandas as pd


random.seed(42)

PAYMENT_METHODS = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Net Banking",
    "Wallet",
]

FAILURE_REASONS = [
    "Insufficient Funds",
    "Card Expired",
    "Network Error",
    "Bank Declined",
    "Transaction Timeout",
]


def generate_case():
    amount = random.choice([
        299, 499, 799, 999, 1499,
        1999, 2499, 4999, 9999, 14999,
        24999, 49999
    ])

    payment_method = random.choice(PAYMENT_METHODS)
    failure_reason = random.choice(FAILURE_REASONS)

    attempts = random.randint(1, 5)

    # Base recovery probability
    probability = 0.50

    # Payment method influence
    method_bonus = {
        "UPI": 0.18,
        "Net Banking": 0.15,
        "Credit Card": 0.08,
        "Debit Card": 0.05,
        "Wallet": 0.02,
    }

    probability += method_bonus[payment_method]

    # Failure reason influence
    reason_bonus = {
        "Insufficient Funds": 0.05,
        "Card Expired": -0.15,
        "Network Error": 0.10,
        "Bank Declined": -0.12,
        "Transaction Timeout": 0.06,
    }

    probability += reason_bonus[failure_reason]

    # More attempts usually means lower chance
    probability -= (attempts - 1) * 0.06

    # Smaller transactions are generally easier to recover
    if amount <= 2000:
        probability += 0.10
    elif amount >= 20000:
        probability -= 0.08

    probability = max(0.05, min(0.95, probability))

    recovered = random.random() < probability

    return {
        "amount": amount,
        "payment_method": payment_method,
        "failure_reason": failure_reason,
        "attempt_count": attempts,
        "recovered": int(recovered),
    }


def main():
    rows = [generate_case() for _ in range(1000)]

    df = pd.DataFrame(rows)

    output_path = Path("app/ml/training_data.csv")
    df.to_csv(output_path, index=False)

    print("\n========== TRAINING DATA ==========")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Saved to: {output_path}")

    print("\n========== SAMPLE ==========")
    print(df.head(10).to_string(index=False))

    print("\n========== OUTCOME DISTRIBUTION ==========")
    print(df["recovered"].value_counts())


if __name__ == "__main__":
    main()