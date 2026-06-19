import asyncio
import sys
import os
sys.path.append(os.getcwd())

# Environment will be picked up from libs.config or default session behavior

from workers.workflow_worker.tasks.project_tasks import run_project_task
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from sqlalchemy import select

async def trigger():
    from libs.db.session import DATABASE_URL
    print(f"DEBUG: Using DATABASE_URL={DATABASE_URL}")
    async with AsyncSessionLocal() as db:

        # Get a project that is stuck
        p_id = "93be3249-2d45-40a6-96e2-eaa9dcf31312"
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
