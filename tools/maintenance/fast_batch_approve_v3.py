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
from sqlalchemy import text
from apps.worker.tasks.celery_app import celery_app

async def fast_batch_approve():
    print("🚀 Starting Fast Batch Approval (V3 - Hardened)...")
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch all suggested tasks using raw SQL to be sure
        res = await db.execute(text("SELECT id, title, description, priority, owner_agent_hint, reasoning_summary FROM ceo_suggested_tasks WHERE status = 'suggested'"))
        suggestions = res.fetchall()
        
        count = len(suggestions)
        print(f"📦 Found {count} suggested tasks in DB.")
        
        if count == 0:
            print("✅ No tasks found in 'suggested' status.")
            return

        approved_count = 0
        for sug_id, sug_title, sug_desc, sug_prio, sug_hint, sug_reason in suggestions:
            try:
                # 2. Create Project
                proj_id = uuid.uuid4()
                new_project = Project(
                    id=proj_id,
                    title=f"[CEO-AUTO] {sug_title}",
                    description=sug_desc,
                    status=ProjectStatus.PENDING,
                    priority=sug_prio or "medium",
                    assigned_agent=sug_hint or "architect",
                    suggestion_id=sug_id,
                    ceo_managed=True,
                    workflow_template="default",
                    quality_profile="production",
                    notes=f"CEO Dashboard üzerinden toplu onaylandı. Gerekçesi: {sug_reason}"
                )
                db.add(new_project)
                
                # 3. Update Suggestion status via raw SQL to bypass ORM mapping issues
                await db.execute(text("UPDATE ceo_suggested_tasks SET status = 'approved', created_task_id = :tid WHERE id = :sid"), 
                                 {"tid": proj_id, "sid": sug_id})
                
                # 4. Enqueue
                celery_task = celery_app.send_task(
                    "tasks.project_tasks.run_project_task",
                    args=[str(proj_id), f"[CEO-AUTO] {sug_title}", sug_desc],
                    kwargs={"workflow_template": "default", "quality_profile": "production"}
                )
                
                new_project.status = ProjectStatus.QUEUED
                new_project.job_id = celery_task.id
                
                approved_count += 1
                if approved_count % 10 == 0:
                    print(f"✅ Processed {approved_count}/{count}...")
                
            except Exception as e:
                print(f"❌ Error approving task {sug_id}: {e}")

        await db.commit()
        print(f"🏁 Batch Approval Complete! {approved_count} tasks approved and queued.")

if __name__ == "__main__":
    asyncio.run(fast_batch_approve())
