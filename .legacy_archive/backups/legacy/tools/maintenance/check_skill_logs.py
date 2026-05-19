import asyncio
from packages.persistence.session import AsyncSessionLocal
from sqlalchemy import select
from packages.persistence.models import SkillExecutionLog

async def check_logs():
    async with AsyncSessionLocal() as db:
        stmt = select(SkillExecutionLog).limit(10)
        result = await packages.persistence.execute(stmt)
        logs = result.scalars().all()
        print(f"Total logs found: {len(logs)}")
        for log in logs:
            print(f"- Skill: {log.skill_id}, Success: {log.success}, Duration: {log.duration_s}s")

if __name__ == "__main__":
    asyncio.run(check_logs())
