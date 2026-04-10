import asyncio
import os
import uuid
import sys
import logging
import traceback
import json
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from packages.persistence.session import AsyncSessionLocal
from sqlalchemy import text

async def final_push():
    print("🚀 SISTEM AKTIFLESTIRME (Schema-Aware Mod)...")
    
    try:
        async with AsyncSessionLocal() as db:
            res = await db.execute(text("SELECT id, title, description FROM ceo_suggested_tasks WHERE status = 'suggested'"))
            rows = res.fetchall()
            print(f"📦 {len(rows)} adet öneri bulundu.")
            
            if not rows:
                print("✅ Onaylanacak yeni gorev kalmadi.")
                return

        approved_count = 0
        for r_id, r_title, r_desc in rows:
            async with AsyncSessionLocal() as db_task:
                try:
                    p_id = uuid.uuid4()
                    
                    # 2. Insert Project (Including reviews and review_required)
                    sql = """
                        INSERT INTO projects (
                            id, title, description, status, priority, source, 
                            workflow_template, quality_profile, review_required, reviews,
                            created_at, updated_at
                        )
                        VALUES (
                            CAST(:pid AS UUID), :title, :desc, 'QUEUED', 'medium', 'api', 
                            'default', 'production', false, '[]'::jsonb,
                            now(), now()
                        )
                    """
                    await db_task.execute(text(sql), {
                        "pid": str(p_id),
                        "title": f"[CEO-AUTO] {r_title}",
                        "desc": r_desc or ""
                    })
                    
                    # 3. Update Suggestion
                    await db_task.execute(text("UPDATE ceo_suggested_tasks SET status = 'approved', created_task_id = CAST(:tid AS UUID) WHERE id = CAST(:sid AS UUID)"), 
                                     {"tid": str(p_id), "sid": str(r_id)})
                    
                    await db_task.commit()
                    approved_count += 1
                    if approved_count % 10 == 0:
                        print(f"✅ {approved_count}/{len(rows)} tamamlandi...")
                    
                except Exception:
                    print(f"❌ Gorev {r_id} hatasi:")
                    traceback.print_exc()
                    await db_task.rollback()

        print(f"🏁 SKOR: {approved_count}/{len(rows)} basarili.")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(final_push())
