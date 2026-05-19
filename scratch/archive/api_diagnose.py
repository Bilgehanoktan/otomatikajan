
import asyncio
from sqlalchemy import select, func
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project

async def diagnose():
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(Project.status, func.count(Project.id).label("cnt")).group_by(Project.status)
        )
        rows = res.all()
        print("API Perspective (DB Rows):")
        for row in rows:
            status_val = str(row.status.value).lower() if hasattr(row.status, "value") else str(row.status).lower()
            print(f"Status: {row.status} (Lower: {status_val}), Count: {row.cnt}")
        
        total = sum(row.cnt for row in rows)
        print(f"Total: {total}")

if __name__ == "__main__":
    asyncio.run(diagnose())
