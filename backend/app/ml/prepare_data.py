import asyncio
from pathlib import Path

import pandas as pd

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.repositories.entities import (
    get_payment_repository,
    get_payment_attempt_repository,
    get_recovery_case_repository,
)


async def prepare_dataset():
    await connect_to_mongo()

    try:
        payment_repo = get_payment_repository()
        attempt_repo = get_payment_attempt_repository()
        recovery_repo = get_recovery_case_repository()

        payments = await payment_repo.find_many(limit=10000)
        attempts = await attempt_repo.find_many(limit=10000)
        recovery_cases = await recovery_repo.find_many(limit=10000)

        rows = []

        for payment in payments:
            payment_attempts = [
                a for a in attempts
                if str(a.payment_id) == str(payment.id)
            ]

            recovery_case = next(
                (
                    c for c in recovery_cases
                    if str(c.payment_id) == str(payment.id)
                ),
                None,
            )

            successful_attempts = sum(
                1 for a in payment_attempts
                if a.status.value == "success"
            )

            failed_attempts = sum(
                1 for a in payment_attempts
                if a.status.value == "failed"
            )

            rows.append({
                "amount": payment.amount,
                "payment_method": payment.payment_method,
                "failure_reason": payment.failure_reason or "Unknown",
                "attempt_count": len(payment_attempts),
                "successful_attempts": successful_attempts,
                "failed_attempts": failed_attempts,
                "final_status": payment.status.value,
                "recovery_probability": (
                    recovery_case.recovery_probability
                    if recovery_case
                    else None
                ),
                "recovery_status": (
                    recovery_case.status.value
                    if recovery_case
                    else None
                ),
            })

        df = pd.DataFrame(rows)

        output_path = Path("app/ml/recovery_training_data.csv")
        df.to_csv(output_path, index=False)

        print("\n========== DATASET CREATED ==========")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print(f"Saved to: {output_path}")

        print("\n========== DATA ==========")
        print(df.to_string(index=False))

    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(prepare_dataset())