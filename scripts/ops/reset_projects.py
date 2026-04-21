import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, ProjectStatus
from sqlalchemy import update

async def reset():
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            update(Project)
            .where(Project.title.like('%Workflow%'))
            .values(status=ProjectStatus.PENDING)
        )
        await db.commit()
        print(f"Reset {res.rowcount} projects to PENDING")

if __name__ == "__main__":
    asyncio.run(reset())
