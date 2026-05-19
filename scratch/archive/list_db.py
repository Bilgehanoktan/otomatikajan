import asyncio
import sys
import os
sys.path.insert(0, '.')

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, SubTask
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Project).order_by(Project.created_at.desc()))
        projects = res.scalars().all()
        print(f"Total Projects: {len(projects)}")
        for p in projects:
            print(f"ID: {p.id} | Title: {p.title} | Status: {p.status}")
            
        res_st = await db.execute(select(SubTask).limit(10))
        stasks = res_st.scalars().all()
        print(f"\nRecent SubTasks: {len(stasks)}")
        for st in stasks:
            print(f"  - ID: {st.id} | Project: {st.project_id} | Status: {st.status}")

if __name__ == "__main__":
    asyncio.run(main())
