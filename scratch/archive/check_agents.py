
import asyncio
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import AgentNode
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(AgentNode))
        nodes = res.scalars().all()
        if not nodes:
            print("No agent nodes found.")
        for a in nodes:
            print(f"ID: {a.id}, Name: {a.name}, Role: {a.role}, Score: {a.trust_score}")

if __name__ == "__main__":
    asyncio.run(run())
