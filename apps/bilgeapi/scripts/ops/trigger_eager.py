import asyncio
import sys
import os
sys.path.append(os.getcwd())

# Ensure environment is set
os.environ["REDIS_URL"] = "redis://127.0.0.1:6380/0"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_company"

from workers.workflow_worker.tasks.project_tasks import run_project_task
from workers.workflow_worker.tasks.celery_app import celery_app
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from sqlalchemy import select

# FORCE EAGER MODE (runs in same process)
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

async def trigger():
    async with AsyncSessionLocal() as db:
        # Get Project [Workflow Beta] (ec68e46b-3fa4-4999-89c7-11c4aeff1650)
        p_id = "ec68e46b-3fa4-4999-89c7-11c4aeff1650"
        res = await db.execute(select(Project).where(Project.id == p_id))
        project = res.scalar_one_or_none()
        
        if project:
            print(f"Triggering EAGER task for Project: {project.title} ({project.id})")
            # This will run the task code RIGHT HERE
            result = run_project_task.delay(
                str(project.id), 
                project.title, 
                project.description or "Manual trigger"
            )
            print(f"Eager task result: {result.status}")
        else:
            print("Project not found.")

if __name__ == "__main__":
    asyncio.run(trigger())
