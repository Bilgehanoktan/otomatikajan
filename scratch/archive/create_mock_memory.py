import asyncio
import uuid
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.repair_models import RepairMemory
from datetime import datetime, timezone

async def create_mock():
    async with AsyncSessionLocal() as db:
        mem = RepairMemory(
            id=uuid.uuid4(),
            memory_id="mem_test_" + str(uuid.uuid4())[:8],
            incident_id="inc_888",
            project_id="proj_999",
            cluster_id="cluster_main",
            patch_signature="auth:conservative",
            outcome="success",
            score=0.98,
            recorded_at=datetime.now(timezone.utc)
        )
        db.add(mem)
        await db.commit()
        print("Mock memory created successfully.")

if __name__ == "__main__":
    asyncio.run(create_mock())
