import asyncio
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from sqlalchemy import select

async def verify():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project).filter(Project.title.like("Integration Check%")).order_by(Project.created_at.desc())
        )
        projects = result.scalars().all()
        if projects:
            p = projects[0]
            print(f"✅ VERIFICATION SUCCESS: Project '{p.title}' found in DB.")
            print(f"   ID: {p.id}")
            print(f"   Status: {p.status}")
            print(f"   Budget: ${p.current_budget_usd}")
        else:
            print("❌ VERIFICATION FAILED: Test project not found in DB.")

if __name__ == "__main__":
    asyncio.run(verify())
