
import asyncio
from sqlalchemy import text
from libs.db.session import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("PRAGMA table_info(governor_cases)"))
        print(f"governor_cases: {[r[1] for r in res.fetchall()]}")
        
        res = await db.execute(text("PRAGMA table_info(governor_alerts)"))
        print(f"governor_alerts: {[r[1] for r in res.fetchall()]}")

if __name__ == "__main__":
    asyncio.run(check())
