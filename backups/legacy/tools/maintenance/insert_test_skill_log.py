import asyncio
import uuid
from datetime import datetime
from packages.persistence.session import AsyncSessionLocal
from packages.persistence.models import SkillExecutionLog

async def insert_test_log():
    async with AsyncSessionLocal() as db:
        log = SkillExecutionLog(
            id=uuid.uuid4(),
            project_id=None,
            agent_id="test_agent_alpha",
            skill_id="optimization",
            success=True,
            summary="Test skill execution for dashboard verification.",
            data={"test": "data"},
            duration_s=1.23,
            created_at=datetime.utcnow()
        )
        packages.persistence.add(log)
        await packages.persistence.commit()
        print(f"Inserted test log ID: {log.id}")

if __name__ == "__main__":
    asyncio.run(insert_test_log())
