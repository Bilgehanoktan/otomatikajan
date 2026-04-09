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

async def db_test():
    print(f"--- DB Diagnostic ---")
    print(f"DATABASE_URL Env: {os.getenv('DATABASE_URL')}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check current engine URL
            engine = db.bind
            print(f"Engine URL: {engine.url}")
            
            # Check table counts
            res = await db.execute(text("SELECT count(*) FROM ceo_suggested_tasks"))
            count = res.scalar()
            print(f"ceo_suggested_tasks count: {count}")
            
            res = await db.execute(text("SELECT count(*) FROM projects"))
            count_p = res.scalar()
            print(f"projects count: {count_p}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(db_test())
