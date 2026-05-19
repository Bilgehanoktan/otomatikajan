import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from libs.db.models.core_models import WorkflowTask

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_company')
    async with AsyncSession(engine) as db:
        res = await db.execute(select(WorkflowTask).where(WorkflowTask.project_id == 'edceee75-3f8f-4979-b065-60a81d6cbd1d'))
        tasks = res.scalars().all()
        print(f"Total Tasks: {len(tasks)}")
        for t in tasks:
            print(f"Step: {t.step_id} | Status: {t.status}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
