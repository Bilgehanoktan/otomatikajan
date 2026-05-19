import asyncio
from sqlalchemy import select
from libs.db.session import AsyncSessionLocal
from libs.db.models.learning_models import ErrorFingerprint

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ErrorFingerprint).where(ErrorFingerprint.is_active == True))
        fps = res.scalars().all()
        for fp in fps:
            print(f"ID: {fp.id} | Component: {fp.component}")
            print(f"Message: {fp.normalized_message}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
