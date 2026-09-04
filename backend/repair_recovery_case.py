import asyncio

from app.db.mongodb import connect_to_mongo, get_database, close_mongo_connection
from app.db.collections import RECOVERY_CASES_COLLECTION


async def main():
    await connect_to_mongo()

    db = get_database()

    if db is None:
        print("MongoDB is not connected.")
        return

    collection = db[RECOVERY_CASES_COLLECTION]

    result = await collection.update_many(
        {"recommended_action": "string"},
        {"$set": {"recommended_action": "SMART_RETRY"}},
    )

    print(f"Recovery cases repaired: {result.modified_count}")

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())