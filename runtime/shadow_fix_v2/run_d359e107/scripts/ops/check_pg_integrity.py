import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SubTask, Project
from sqlalchemy import select, func

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Project).order_by(Project.created_at.desc()))
        projects = res.scalars().all()
        print(f"Total Projects in PG: {len(projects)}")
        
        for p in projects:
            st_res = await db.execute(select(func.count(SubTask.id)).where(SubTask.project_id == p.id))
            count = st_res.scalar()
            if count > 0:
                print(f"Project [{p.title}] ({p.id}) -> {count} steps")
            elif "Workflow Beta" in p.title or "474fc58f" in str(p.id):
                print(f"Project [{p.title}] ({p.id}) -> 0 steps (CRITICAL)")

if __name__ == "__main__":
    asyncio.run(check())
