import asyncio
import sys
import os
sys.path.append(os.getcwd())

# Ensure environment is set
os.environ["REDIS_URL"] = "redis://127.0.0.1:6380/0"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_company"

from workers.workflow_worker.tasks.project_tasks import run_project_task
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, ProjectStatus, ProjectSource, TaskPriority
import uuid

async def trigger():
    async with AsyncSessionLocal() as db:
        # Create a FRESH project
        new_id = uuid.uuid4()
        new_project = Project(
            id=new_id,
            title="Workflow Final (Post-Fix)",
            description="Verifying that 3 steps are persisted correctly in PG.",
            status=ProjectStatus.PENDING,
            source=ProjectSource.CONTROL_PLANE,
            priority=TaskPriority.HIGH
        )
        db.add(new_project)
        await db.commit()
        
        print(f"Created fresh Project: {new_project.title} ({new_id})")
        
        # Trigger task to debug_queue
        result = run_project_task.apply_async(
            args=[str(new_id), "Workflow Final (Post-Fix)", "Verifying that 3 steps are persisted correctly in PG."],
            queue="debug_queue"
        )
        print(f"Task sent to debug_queue! Task ID: {result.id}")
        return new_id

if __name__ == "__main__":
    asyncio.run(trigger())
