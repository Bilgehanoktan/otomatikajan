import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SubTask
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(SubTask))
        subtasks = res.scalars().all()
        print(f"Total SubTasks in PG: {len(subtasks)}")
        
        for st in subtasks:
            print(f"SubTask [{st.id}] -> Project [{st.project_id}]")

if __name__ == "__main__":
    asyncio.run(check())
