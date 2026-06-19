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
        new_project = Project(
            id=uuid.uuid4(),
            title="Workflow Omega (Final Debug)",
            description="Testing via debug_queue.",
            status=ProjectStatus.PENDING,
            source=ProjectSource.CONTROL_PLANE,
            priority=TaskPriority.HIGH
        )
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)
        
        print(f"Created fresh Project: {new_project.title} ({new_project.id})")
        
        # Trigger task to debug_queue
        result = run_project_task.apply_async(
            args=[str(new_project.id), new_project.title, new_project.description],
            queue="debug_queue"
        )
        print(f"Task sent to debug_queue! Task ID: {result.id}")

if __name__ == "__main__":
    asyncio.run(trigger())
