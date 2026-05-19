
import asyncio
import uuid
from sqlalchemy import select, func
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, ProjectStatus

async def check_projects():
    async with AsyncSessionLocal() as db:
        # Son 10 projeyi getir
        result = await db.execute(select(Project).order_by(Project.created_at.desc()).limit(10))
        projects = result.scalars().all()
        
        print(f"--- SON 10 PROJE ---")
        for p in projects:
            print(f"ID: {p.id} | Title: {p.title} | Status: {p.status} | Created: {p.created_at}")
        
        # Status dağılımı
        result = await db.execute(select(Project.status, func.count(Project.id)).group_by(Project.status))
        counts = result.all()
        print(f"\n--- STATUS DAĞILIMI ---")
        for s, c in counts:
            print(f"{s}: {c}")

if __name__ == "__main__":
    asyncio.run(check_projects())
