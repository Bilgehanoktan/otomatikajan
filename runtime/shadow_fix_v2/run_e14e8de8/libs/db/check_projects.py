
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import text

from libs.db.session import AsyncSessionLocal, get_engine


async def check():
    engine = get_engine()
    print(f"[*] Active Engine: {engine.url}")

    async with AsyncSessionLocal() as db:
        try:
            res = await db.execute(text("SELECT count(*) FROM projects"))
            count = res.scalar()
            print(f"[*] Project Count: {count}")

            res = await db.execute(text("SELECT id, title, status, priority FROM projects ORDER BY created_at DESC LIMIT 5"))
            rows = res.all()
            for r in rows:
                print(f"  - {r.id}: {r.title} ({r.status}) [Priority: {r.priority}]")
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
