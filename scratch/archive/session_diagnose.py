
import asyncio
from sqlalchemy import select, func
from libs.db.session import AsyncSessionLocal, get_engine
from libs.db.models.core_models import Project

async def diagnose():
    engine = get_engine()
    print(f"Engine URL: {engine.url}")
    
    async with AsyncSessionLocal() as session:
        # Check current session engine
        s_engine = session.get_bind()
        print(f"Session Engine URL: {s_engine.url}")
        
        count = await session.scalar(select(func.count(Project.id)))
        print(f"Project Count (via AsyncSessionLocal): {count}")

if __name__ == "__main__":
    asyncio.run(diagnose())
