import asyncio
from app.repositories.entities import get_recovery_case_repository

async def main():
    repo = get_recovery_case_repository()

    case_id = "28357bf0-8a00-4d7a-9cfa-0976d2ebe61f"

    deleted = await repo.delete_by_id(case_id)

    print("Deleted:", deleted)

asyncio.run(main())