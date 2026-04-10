import asyncio
import os
import uuid
import sys
import logging
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Enable SQLAlchemy logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from packages.persistence.session import AsyncSessionLocal
from sqlalchemy import text
from apps.worker.tasks.celery_app import celery_app

async def nuclear_approve():
    print("🚀 Starting NUCLEAR Batch Approval (V2)...")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch
            print("🔍 Fetching suggested tasks...")
            res = await db.execute(text("SELECT id, title, description FROM ceo_suggested_tasks WHERE status = 'suggested'"))
            rows = res.fetchall()
            print(f"📦 Found {len(rows)} tasks.")
            
            if not rows:
                return

            approved_count = 0
            for r_id, r_title, r_desc in rows:
                try:
                    p_id = uuid.uuid4()
                    print(f"🔨 Processing task: {r_id} -> New Project: {p_id}")
                    
                    # 2. Insert Project (Using strings for UUIDs to be safe)
                    await db.execute(text("""
                        INSERT INTO projects (id, title, description, status, priority, source, workflow_template, quality_profile, created_at, updated_at)
                        VALUES (:pid, :title, :desc, 'QUEUED', 'medium', 'api', 'default', 'production', now(), now())
                    """), {
                        "pid": str(p_id),
                        "title": f"[CEO-AUTO] {r_title}",
                        "desc": r_desc or ""
                    })
                    
                    # 3. Update Suggestion
                    await db.execute(text("UPDATE ceo_suggested_tasks SET status = 'approved', created_task_id = :tid WHERE id = :sid"), 
                                     {"tid": str(p_id), "sid": str(r_id)})
                    
                    # 4. Enqueue
                    try:
                        celery_app.send_task(
                            "tasks.project_tasks.run_project_task",
                            args=[str(p_id), f"[CEO-AUTO] {r_title}", r_desc or "No description"],
                            kwargs={"workflow_template": "default", "quality_profile": "production"}
                        )
                    except Exception as ce:
                        print(f"⚠️ Celery error (continuing): {ce}")
                    
                    approved_count += 1
                    if approved_count % 5 == 0:
                        print(f"✅ Sub-committing at {approved_count}...")
                        await db.commit()
                        
                except Exception as inner_e:
                    print(f"❌ Inner error on {r_id}: {inner_e}")
                    import traceback
                    traceback.print_exc()

            await db.commit()
            print(f"🏁 Final Commit Done. Total: {approved_count}")
            
        except Exception as e:
            print(f"❌ Outer error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(nuclear_approve())
