import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SubTask
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(SubTask).where(SubTask.agent_id.in_(['plan_subtasks', 'execute_subtasks', 'synthesize_report']))
        )
        items = res.scalars().all()
        print(f"Found {len(items)} workflow steps.")
        for i in items:
            print(f"Step [{i.id}] -> Project [{i.project_id}] ({i.agent_id})")

if __name__ == "__main__":
    asyncio.run(check())
