import asyncio

from app.db.mongodb import (
    connect_to_mongo,
    close_mongo_connection,
    get_database,
)
from app.db.collections import RECOVERY_CASES_COLLECTION


KEEP_ID = "a7998651-104d-4cd8-9df1-aaed461bfd82"

DELETE_IDS = [
    "DEMO_RECOVERY_CASE_1",
    "e3778971-6082-4eb4-9f78-d8175e6bf3a0",
    "55a8d866-cdff-4878-8800-ab4fd50f447e",
]


async def main():
    await connect_to_mongo()

    db = get_database()

    if db is None:
        raise RuntimeError("MongoDB connection failed.")

    collection = db[RECOVERY_CASES_COLLECTION]

    result = await collection.delete_many(
        {
            "id": {"$in": DELETE_IDS},
            "payment_id": "DEMO_PAYMENT_1",
        }
    )

    print(f"Deleted {result.deleted_count} old recovery cases.")
    print(f"Kept current case: {KEEP_ID}")

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())