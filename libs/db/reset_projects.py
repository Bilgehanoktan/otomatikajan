
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import update

from libs.db.models.core_models import Project
from libs.db.session import AsyncSessionLocal


async def reset():
    print("[*] Starting Project Status Reset...")
    async with AsyncSessionLocal() as db:
        stmt = (
            update(Project)
            .where(Project.status.in_(['ERROR', 'FAILED']))
            .values(status='PENDING')
        )
        result = await db.execute(stmt)
        await db.commit()
        print(f"[+] Reset {result.rowcount} projects to PENDING.")

if __name__ == "__main__":
    asyncio.run(reset())
