import asyncio
from libs.db.session import get_db
from libs.db.models.core_models import Project
from sqlalchemy import select

async def list_projects():
    async with get_db() as db:
        res = await db.execute(select(Project).limit(10))
        projects = res.scalars().all()
        for p in projects:
            print(f"ID: {p.id} | Title: {p.title} | Status: {p.status}")

if __name__ == "__main__":
    asyncio.run(list_projects())
