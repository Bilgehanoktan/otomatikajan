import asyncio
import os
import sys

# Proje kök dizinini ekleyelim
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, SubTask
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        # İş akışlarını kontrol et
        res = await db.execute(select(Project))
        projects = res.scalars().all()
        print(f"--- Projects/Workflows ({len(projects)}) ---")
        for p in projects:
            print(f"ID: {p.id} | Status: {p.status} | Title: {p.title}")
            
        # Adımları kontrol et
        res_steps = await db.execute(select(SubTask).where(SubTask.status.in_(["PENDING", "RUNNING", "QUEUED"])))
        stuck_steps = res_steps.scalars().all()
        print(f"\n--- Stuck SubTasks ({len(stuck_steps)}) ---")
        for s in stuck_steps:
            print(f"ID: {s.id} | Project: {s.project_id} | Status: {s.status} | Action: {s.action}")

if __name__ == "__main__":
    asyncio.run(check())
