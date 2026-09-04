from __future__ import annotations

import asyncio

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.models.domain import Payment, PaymentAttempt, PaymentAttemptStatus, PaymentStatus
from app.repositories.entities import (
    get_payment_repository,
    get_payment_attempt_repository,
)


async def main():
    await connect_to_mongo()

    try:
        payment_repo = get_payment_repository()
        attempt_repo = get_payment_attempt_repository()

        merchant_id = "DEMO_MERCHANT_1"

        scenarios = [
            {
                "id": "DEMO_FAILED_HIGH",
                "customer_id": "DEMO_CUSTOMER_HIGH",
                "amount": 999,
                "payment_method": "UPI",
                "failure_reason": "Insufficient Funds",
                "attempts": [],
            },
            {
                "id": "DEMO_FAILED_MEDIUM",
                "customer_id": "DEMO_CUSTOMER_MEDIUM",
                "amount": 2499,
                "payment_method": "CARD",
                "failure_reason": "Transaction Timeout",
                "attempts": [
                    PaymentAttemptStatus.FAILED,
                ],
            },
            {
                "id": "DEMO_FAILED_LOW",
                "customer_id": "DEMO_CUSTOMER_LOW",
                "amount": 7999,
                "payment_method": "CARD",
                "failure_reason": "Card Expired",
                "attempts": [
                    PaymentAttemptStatus.FAILED,
                    PaymentAttemptStatus.FAILED,
                    PaymentAttemptStatus.FAILED,
                ],
            },
        ]

        print("\n========== CREATING DEMO PAYMENTS ==========\n")

        for scenario in scenarios:

            existing = await payment_repo.find_by_id(
                scenario["id"]
            )

            if existing:
                print(f"Already exists: {scenario['id']}")
                continue

            payment = Payment(
                id=scenario["id"],
                merchant_id=merchant_id,
                customer_id=scenario["customer_id"],
                amount=scenario["amount"],
                currency="INR",
                status=PaymentStatus.FAILED,
                payment_method=scenario["payment_method"],
                failure_reason=scenario["failure_reason"],
            )

            await payment_repo.insert(payment)

            for index, status in enumerate(
                scenario["attempts"],
                start=1,
            ):
                attempt = PaymentAttempt(
                    payment_id=payment.id,
                    attempt_number=index,
                    status=status,
                    failure_reason=scenario["failure_reason"],
                )

                await attempt_repo.insert(attempt)

            print(
                f"Created {payment.id} | "
                f"₹{payment.amount} | "
                f"{payment.payment_method} | "
                f"{payment.failure_reason} | "
                f"Attempts: {len(scenario['attempts'])}"
            )

        print("\n========== DONE ==========")

    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())