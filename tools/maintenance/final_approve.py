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
from sqlalchemy import text
from apps.worker.tasks.celery_app import celery_app

async def final_batch_approve():
    print("🚀 Starting FINAL Batch Approval...")
    async with AsyncSessionLocal() as db:
        # 1. Fetch
        res = await db.execute(text("SELECT id, title, description FROM ceo_suggested_tasks WHERE status = 'suggested'"))
        rows = res.fetchall()
        print(f"📦 Found {len(rows)} tasks to approve.")
        
        for r_id, r_title, r_desc in rows:
            try:
                p_id = uuid.uuid4()
                # 2. Insert Project
                await db.execute(text("""
                    INSERT INTO projects (id, title, description, status, priority, assigned_agent, ceo_managed, workflow_template, quality_profile, created_at, updated_at)
                    VALUES (:id, :title, :desc, 'queued', 'medium', 'architect', true, 'default', 'production', now(), now())
                """), {
                    "id": p_id,
                    "title": f"[CEO-AUTO] {r_title}",
                    "desc": r_desc
                })
                
                # 3. Update Suggestion
                await db.execute(text("UPDATE ceo_suggested_tasks SET status = 'approved', created_task_id = :tid WHERE id = :sid"), 
                                 {"tid": p_id, "sid": r_id})
                
                # 4. Enqueue
                celery_app.send_task(
                    "tasks.project_tasks.run_project_task",
                    args=[str(p_id), f"[CEO-AUTO] {r_title}", r_desc or "No description"],
                    kwargs={"workflow_template": "default", "quality_profile": "production"}
                )
                print(f"✅ Approved: {r_id}")
            except Exception as e:
                print(f"❌ Error on {r_id}: {e}")
        
        await db.commit()
    print("🏁 Done.")

if __name__ == "__main__":
    asyncio.run(final_batch_approve())
