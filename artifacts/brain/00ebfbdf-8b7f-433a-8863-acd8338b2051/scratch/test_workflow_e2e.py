
import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.append("/app")

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, SubTask, ProjectStatus, ProjectSource, TaskPriority
from libs.db.repositories.repository import ProjectRepository
from services.orchestration.application.job_queue import job_queue

async def run_test():
    print("Starting E2E Workflow Test...")
    
    async with AsyncSessionLocal() as db:
        # 1. Create Project
        project = await ProjectRepository.create(
            db,
            title="E2E Validation Workflow - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            description="Testing Phase 3.3 End-to-End connectivity and execution.",
            workflow_template="default",
            quality_profile="standard",
            priority="MEDIUM",
            source=ProjectSource.CONTROL_PLANE
        )
        await db.commit()
        await db.refresh(project)
        print(f"Project created: {project.id} ({project.title})")
        
        # 2. Enqueue
        await job_queue.enqueue(
            "run_project",
            project_id=str(project.id),
            title=project.title,
            description=project.description or "",
            workflow_template=project.workflow_template or "default",
            quality_profile=project.quality_profile or "standard",
        )
        print(f"Project enqueued.")
        
        # 3. Monitor
        print("Monitoring workflow (timeout 60s)...")
        for i in range(60):
            await asyncio.sleep(1)
            await db.refresh(project)
            
            # Check subtasks count
            res_st = await db.execute(
                select(SubTask).where(SubTask.project_id == project.id)
            )
            subtasks = res_st.scalars().all()
            
            completed = [st for st in subtasks if st.status in [ProjectStatus.COMPLETED, "COMPLETED"]]
            failed = [st for st in subtasks if st.status in [ProjectStatus.ERROR, "ERROR", ProjectStatus.FAILED, "FAILED"]]
            
            print(f"[{i}s] Status: {project.status} | Steps: {len(subtasks)} | Completed: {len(completed)} | Failed: {len(failed)}")
            
            if project.status in [ProjectStatus.COMPLETED, ProjectStatus.ERROR, ProjectStatus.FAILED]:
                print(f"Workflow reached terminal state: {project.status}")
                break
        else:
            print("Monitoring timed out.")

if __name__ == "__main__":
    from sqlalchemy import select
    asyncio.run(run_test())
