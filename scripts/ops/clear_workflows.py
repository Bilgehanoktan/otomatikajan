import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from sqlalchemy import delete

async def clear():
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            delete(Project).where(Project.title.like('%Workflow%'))
        )
        await db.commit()
        print(f"Deleted {res.rowcount} projects")

if __name__ == "__main__":
    asyncio.run(clear())
