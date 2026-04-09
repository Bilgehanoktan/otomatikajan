import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from packages.persistence.session import AsyncSessionLocal
from sqlalchemy import text

async def data_peek():
    print(f"--- Data Peek ---")
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id, status FROM ceo_suggested_tasks LIMIT 5"))
        rows = res.fetchall()
        print(f"Total rows fetched (any status): {len(rows)}")
        for r in rows:
            print(f"ID: {r[0]}, Status: '{r[1]}'")
        
        res_suggested = await db.execute(text("SELECT count(*) FROM ceo_suggested_tasks WHERE status = 'suggested'"))
        count = res_suggested.scalar()
        print(f"Count with status='suggested' (text query): {count}")

if __name__ == "__main__":
    asyncio.run(data_peek())
