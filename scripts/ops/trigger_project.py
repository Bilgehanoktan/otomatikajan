import asyncio
import sys
import os
sys.path.append(os.getcwd())

# Ensure environment is set
os.environ["REDIS_URL"] = "redis://127.0.0.1:6380/0"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_company"

from workers.workflow_worker.tasks.project_tasks import run_project_task
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from sqlalchemy import select

async def trigger():
    async with AsyncSessionLocal() as db:
        # Get a project with 0 steps
        # Project [Workflow Beta] (ec68e46b-3fa4-4999-89c7-11c4aeff1650)
        p_id = "ec68e46b-3fa4-4999-89c7-11c4aeff1650"
        res = await db.execute(select(Project).where(Project.id == p_id))
        project = res.scalar_one_or_none()
        
        if project:
            print(f"Triggering task for Project: {project.title} ({project.id})")
            # Send task to Celery with all required arguments
            # Signature: db_project_id, title, description
            result = run_project_task.delay(
                str(project.id), 
                project.title, 
                project.description or "Manual trigger"
            )
            print(f"Task sent to Celery! Task ID: {result.id}")
        else:
            print("Project not found.")

if __name__ == "__main__":
    asyncio.run(trigger())
