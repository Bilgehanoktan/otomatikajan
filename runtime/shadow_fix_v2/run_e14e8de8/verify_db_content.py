import asyncio
import sys
sys.path.insert(0, '.')
from libs.db.session import AsyncSessionLocal, init_db
from libs.db.models.core_models import Project, AgentNode, FleetCluster
from sqlalchemy import select

async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        projects = await db.execute(select(Project))
        print("Projects:", [(p.title, p.status) for p in projects.scalars().all()])
        
        agents = await db.execute(select(AgentNode))
        print("Agents:", [(a.name, a.status) for a in agents.scalars().all()])
        
        clusters = await db.execute(select(FleetCluster))
        print("Clusters:", [(c.name, c.status) for c in clusters.scalars().all()])

if __name__ == "__main__":
    asyncio.run(main())
