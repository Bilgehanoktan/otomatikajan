
import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from sqlalchemy import text

async def list_all_projects():
    async with AsyncSessionLocal() as db:
        print("--- All Projects ---")
        query = text("SELECT id, title, status FROM projects")
        results = await db.execute(query)
        for p in results.fetchall():
            print(f"ID: {p.id} | Title: {p.title} | Status: {p.status}")

if __name__ == "__main__":
    asyncio.run(list_all_projects())
