import asyncio

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.agent.recovery_agent import run_recovery_agent


async def main():
    await connect_to_mongo()

    payment_id = "fec3a8f3-cc93-49ef-b72d-3a40364cb09d"

    result = await run_recovery_agent(payment_id)

    print("\n========== RECOVERY AGENT RESULT ==========")
    print(result)

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())