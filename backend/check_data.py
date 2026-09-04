import asyncio

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.repositories.entities import (
    get_payment_repository,
    get_payment_attempt_repository,
    get_recovery_case_repository,
)


async def main():
    await connect_to_mongo()

    try:
        payment_repo = get_payment_repository()
        attempt_repo = get_payment_attempt_repository()
        recovery_repo = get_recovery_case_repository()

        payments = await payment_repo.find_many(limit=10000)
        attempts = await attempt_repo.find_many(limit=10000)
        recovery_cases = await recovery_repo.find_many(limit=10000)

        print("\n========== PAYMENTS ==========")

        for payment in payments:
            print(payment.model_dump(mode="json"))

        print("\n========== PAYMENT ATTEMPTS ==========")

        for attempt in attempts:
            print(attempt.model_dump(mode="json"))

        print("\n========== RECOVERY CASES ==========")

        for case in recovery_cases:
            print(case.model_dump(mode="json"))

        print("\n========== COUNTS ==========")
        print(f"Payments: {len(payments)}")
        print(f"Payment attempts: {len(attempts)}")
        print(f"Recovery cases: {len(recovery_cases)}")

    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())