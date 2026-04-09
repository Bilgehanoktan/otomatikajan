import asyncio
import os
import uuid
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from packages.persistence.session import AsyncSessionLocal
from packages.persistence.models.core_models import CEOSuggestedTask, Project, ProjectStatus
from sqlalchemy import select, update
from apps.worker.tasks.celery_app import celery_app

async def fast_batch_approve():
    print("🚀 Starting Fast Batch Approval (V3)...")
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch all suggested tasks
        stmt = select(CEOSuggestedTask).where(CEOSuggestedTask.status == "suggested")
        res = await db.execute(stmt)
        suggestions = res.scalars().all()
        
        count = len(suggestions)
        print(f"📦 Found {count} suggested tasks.")
        
        if count == 0:
            print("✅ No tasks to approve.")
            return

        approved_count = 0
        for sug in suggestions:
            try:
                # 2. Create Project
                proj_id = uuid.uuid4()
                new_project = Project(
                    id=proj_id,
                    title=f"[CEO-AUTO] {sug.title}",
                    description=sug.description,
                    status=ProjectStatus.PENDING,
                    priority=sug.priority or "medium",
                    assigned_agent=sug.owner_agent_hint or "architect",
                    suggestion_id=sug.id,
                    ceo_managed=True,
                    workflow_template="default",
                    quality_profile="production",
                    notes=f"CEO Dashboard üzerinden toplu onaylandı. Gerekçesi: {sug.reasoning_summary}"
                )
                db.add(new_project)
                
                # 3. Update Suggestion
                sug.status = "approved"
                sug.created_task_id = proj_id
                
                # 4. Enqueue
                celery_task = celery_app.send_task(
                    "tasks.project_tasks.run_project_task",
                    args=[str(proj_id), new_project.title, new_project.description],
                    kwargs={"workflow_template": "default", "quality_profile": "production"}
                )
                
                new_project.status = ProjectStatus.QUEUED
                new_project.job_id = celery_task.id
                
                approved_count += 1
                if approved_count % 10 == 0:
                    print(f"✅ Approved {approved_count}/{count}...")
                
            except Exception as e:
                print(f"❌ Error approving task {sug.id}: {e}")

        await db.commit()
        print(f"🏁 Batch Approval Complete! {approved_count} tasks approved and queued.")

if __name__ == "__main__":
    # Check if we are running in the right environment
    # On host, we might need to override DATABASE_URL to use localhost:5433
    if os.name == 'nt' and "db:5432" in os.getenv("DATABASE_URL", ""):
        db_url = os.getenv("DATABASE_URL").replace("db:5432", "localhost:5433")
        os.environ["DATABASE_URL"] = db_url
        print(f"🔧 Overriding DATABASE_URL for Host: {db_url}")

    asyncio.run(fast_batch_approve())
