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
    print("🚀 Starting FINAL Batch Approval (Traceback Edition)...")
    async with AsyncSessionLocal() as db:
        try:
            res = await db.execute(text("SELECT id, title, description, priority, owner_agent_hint, reasoning_summary FROM ceo_suggested_tasks WHERE status = 'suggested' LIMIT 1"))
            rows = res.fetchall()
            if not rows:
                print("No tasks found.")
                return
            
            sug_id, sug_title, sug_desc, sug_prio, sug_hint, sug_reason = rows[0]
            
            proj_id = uuid.uuid4()
            new_project = Project(
                id=proj_id,
                title=f"[CEO-AUTO] {sug_title}",
                status=ProjectStatus.QUEUED,
                source=ProjectSource.API,
                priority=TaskPriority.MEDIUM,
                workflow_template="default",
                quality_profile="production"
            )
            db.add(new_project)
            await db.commit()
            print("✅ Success on 1 task.")
        except Exception:
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(final_batch_approve())
