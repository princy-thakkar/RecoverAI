import asyncio

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.models.domain import Payment, PaymentStatus
from app.repositories.entities import get_payment_repository


async def main():
    await connect_to_mongo()

    repo = get_payment_repository()

    payment = Payment(
        merchant_id="DEMO_MERCHANT_1",
        customer_id="DEMO_CUSTOMER_1",
        amount=1800,
        currency="INR",
        status=PaymentStatus.FAILED,
        payment_method="UPI",
        failure_reason="Insufficient Funds",
    )

    await repo.insert(payment)

    print("Created test payment:")
    print(payment.model_dump(mode="json"))

    await close_mongo_connection()


asyncio.run(main())