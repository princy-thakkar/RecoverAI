import asyncio
from app.repositories.entities import get_payment_repository

async def main():
    repo = get_payment_repository()
    payments = await repo.find_many(limit=1000)

    print("PAYMENTS:")
    for p in payments:
        print(p)

asyncio.run(main())
