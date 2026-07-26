import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SubTask
from sqlalchemy import select
from uuid import UUID

async def check():
    async with AsyncSessionLocal() as db:
        p_id = 'bea49a4e-e013-4c44-9790-dda2869d76cf'
        res = await db.execute(select(SubTask).where(SubTask.project_id == UUID(p_id)))
        tasks = res.scalars().all()
        print(f"Steps for Omega: {len(tasks)}")
        for t in tasks:
            print(f" - {t.id} | {t.action} | {t.status}")

if __name__ == "__main__":
    asyncio.run(check())
