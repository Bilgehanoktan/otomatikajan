import asyncio
import os
import uuid
import sys
import traceback
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from packages.persistence.session import AsyncSessionLocal
from packages.persistence.models.core_models import CEOSuggestedTask, Project, ProjectStatus, TaskPriority, ProjectSource
from sqlalchemy import text
from apps.worker.tasks.celery_app import celery_app

async def final_batch_approve():
    print("🚀 Starting UNSTOPPABLE Batch Approval...")
    async with AsyncSessionLocal() as db:
        # 1. Fetch
        res = await db.execute(text("SELECT id, title, description, priority, owner_agent_hint, reasoning_summary FROM ceo_suggested_tasks WHERE status = 'suggested'"))
        rows = res.fetchall()
        print(f"📦 Found {len(rows)} tasks to approve.")
        
        approved_count = 0
        for sug_id, sug_title, sug_desc, sug_prio, sug_hint, sug_reason in rows:
            try:
                # 2. Create Project
                proj_id = uuid.uuid4()
                new_project = Project(
                    id=proj_id,
                    title=f"[CEO-AUTO] {sug_title}",
                    description=sug_desc or "",
                    status=ProjectStatus.QUEUED,
                    priority=TaskPriority.MEDIUM, # Keep it simple
                    source=ProjectSource.API,
                    assigned_agent=sug_hint or "architect",
                    workflow_template="default",
                    quality_profile="production",
                    notes=f"CEO Dashboard üzerinden toplu onaylandı. Gerekçesi: {sug_reason}"
                )
                db.add(new_project)
                
                # 3. Update Suggestion
                await db.execute(text("UPDATE ceo_suggested_tasks SET status = 'approved', created_task_id = :tid WHERE id = :sid"), 
                                 {"tid": proj_id, "sid": sug_id})
                
                # 4. Enqueue
                try:
                    celery_task = celery_app.send_task(
                        "tasks.project_tasks.run_project_task",
                        args=[str(proj_id), f"[CEO-AUTO] {sug_title}", sug_desc or "No description"],
                        kwargs={"workflow_template": "default", "quality_profile": "production"}
                    )
                    new_project.job_id = celery_task.id
                except Exception as ce:
                    print(f"⚠️ Celery enqueue failed for {proj_id}, but project created: {ce}")

                approved_count += 1
                if approved_count % 10 == 0:
                    print(f"✅ Processed {approved_count}/{len(rows)}...")
                
                # Partial commit for each 10 tasks to prevent big transaction failure
                if approved_count % 10 == 0:
                    await db.commit()

            except Exception as e:
                print(f"❌ Error on {sug_id}: {e}")
                # traceback.print_exc()
        
        await db.commit()
    print(f"🏁 Done. Total Approved: {approved_count}")

if __name__ == "__main__":
    asyncio.run(final_batch_approve())
