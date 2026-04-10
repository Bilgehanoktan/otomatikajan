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

from packages.persistence.session import AsyncSessionLocal
from sqlalchemy import text
from apps.worker.tasks.celery_app import celery_app

async def final_push():
    print("🚀 SISTEM AKTIFLESTIRME: 90+ Gorev Onaylaniyor...")
    async with AsyncSessionLocal() as db:
        # 1. Fetch
        res = await db.execute(text("SELECT id, title, description FROM ceo_suggested_tasks WHERE status = 'suggested'"))
        rows = res.fetchall()
        print(f"📦 {len(rows)} adet öneri bulundu.")
        
        if not rows:
            print("✅ Onaylanacak yeni gorev kalmadi.")
            return

        approved_count = 0
        for r_id, r_title, r_desc in rows:
            try:
                p_id = uuid.uuid4()
                # 2. Insert Project with explicit CAST for UUID stability
                await db.execute(text("""
                    INSERT INTO projects (id, title, description, status, priority, source, workflow_template, quality_profile, created_at, updated_at)
                    VALUES (CAST(:pid AS UUID), :title, :desc, 'QUEUED', 'medium', 'api', 'default', 'production', now(), now())
                """), {
                    "pid": str(p_id),
                    "title": f"[CEO-AUTO] {r_title}",
                    "desc": r_desc or ""
                })
                
                # 3. Update Suggestion
                await db.execute(text("UPDATE ceo_suggested_tasks SET status = 'approved', created_task_id = CAST(:tid AS UUID) WHERE id = CAST(:sid AS UUID)"), 
                                 {"tid": str(p_id), "sid": str(r_id)})
                
                # 4. Enqueue to Celery
                try:
                    celery_app.send_task(
                        "tasks.project_tasks.run_project_task",
                        args=[str(p_id), f"[CEO-AUTO] {r_title}", r_desc or "No description"],
                        kwargs={"workflow_template": "default", "quality_profile": "production"}
                    )
                except Exception as ce:
                    print(f"⚠️ Celery uyarisi (gorev kuyruklanamadi): {ce}")
                
                approved_count += 1
                if approved_count % 10 == 0:
                    print(f"✅ {approved_count}/{len(rows)} islendi...")
                    await db.commit() # Per 10 commit for safety
                    
            except Exception as e:
                print(f"❌ Hata (Gorev {r_id}): {e}")

        await db.commit()
    print(f"🏁 ISLEM TAMAMLANDI: Toplam {approved_count} gorev onaylandi ve kuyruga eklendi.")

if __name__ == "__main__":
    asyncio.run(final_push())
