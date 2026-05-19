
import asyncio
import os
import sys

# Set path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from libs.db.session import init_db, AsyncSessionLocal
from libs.db.models.core_models import AgentNode
from sqlalchemy import select

async def run():
    from libs.db.session import get_engine
    engine = get_engine()
    print(f"DEBUG: SQLite Path -> {engine.url}")
    
    print("Running init_db()...")
    await init_db()
    print("init_db() completed.")
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(AgentNode))
        nodes = res.scalars().all()
        print(f"Found {len(nodes)} agent nodes.")
        for a in nodes:
            print(f"ID: {a.id}, Name: {a.name}, Role: {a.role}, Score: {a.trust_score}, Success: {a.success_count}")

if __name__ == "__main__":
    asyncio.run(run())
