import asyncio
import uuid
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from sqlalchemy import select

async def check_p(): 
    try:
        target_id = uuid.UUID('6bf72fb5-7cd8-4d9e-b928-54af95867c64')
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Project).where(Project.id == target_id))
            p = res.scalar_one_or_none()
            if p:
                print(f"FOUND: {p.title} (Status: {p.status})")
            else:
                print("NOT FOUND")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_p())
