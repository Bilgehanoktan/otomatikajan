import asyncio
import sys
import os

# Add workspace to path
sys.path.append(os.getcwd())

from libs.db.session import async_session_factory
from libs.db.models.core_models import SubTask, Project
from sqlalchemy import select

async def debug_db():
    async with async_session_factory() as session:
        # Check specific ID from screenshot
        target_id = '474fc58f-c384-40f0-bf6f-c59d1e486e37'
        res = await session.execute(select(SubTask).where(SubTask.parent_id == target_id))
        items = res.scalars().all()
        print(f"--- DB DEBUG ---")
        print(f"Workflow ID: {target_id}")
        print(f"Steps found: {len(items)}")
        
        # Check all subtasks
        res_st = await session.execute(select(SubTask))
        all_st = res_st.scalars().all()
        print(f"Total SubTasks in DB: {len(all_st)}")

        # Check all projects
        res2 = await session.execute(select(Project))
        projects = res2.scalars().all()
        print(f"Total Workflows: {len(projects)}")
        for p in projects[:5]:
            # Try name or title
            name = getattr(p, 'name', getattr(p, 'title', 'Unknown'))
            print(f"  - {name} ({p.id})")

if __name__ == "__main__":
    asyncio.run(debug_db())
