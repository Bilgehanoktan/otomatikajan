import asyncio
import os
import uuid
import sys
import logging
import traceback
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from packages.persistence.session import AsyncSessionLocal
from packages.persistence.models.core_models import Project, ProjectStatus, ProjectSource, TaskPriority, CEOSuggestedTask
from sqlalchemy import select, update

async def final_push():
    print("🚀 SISTEM AKTIFLESTIRME (ORM Saf Mod)...")
    
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(CEOSuggestedTask).where(CEOSuggestedTask.status == 'suggested')
            res = await db.execute(stmt)
            tasks = res.scalars().all()
            print(f"📦 {len(tasks)} adet öneri bulundu.")
            
            if not tasks:
                print("✅ Onaylanacak yeni gorev kalmadi.")
                return

        approved_count = 0
        for task in tasks:
            async with AsyncSessionLocal() as db_task:
                try:
                    p_id = uuid.uuid4()
                    
                    # Create Project using ORM
                    new_project = Project(
                        id=p_id,
                        title=f"[CEO-AUTO] {task.title}",
                        description=task.description or "",
                        status=ProjectStatus.QUEUED,
                        priority=TaskPriority.MEDIUM,
                        source=ProjectSource.API,
                        workflow_template="default",
                        quality_profile="production"
                    )
                    db_task.add(new_project)
                    
                    # Update Task status
                    # We need to fetch the task in this session or use update()
                    await db_task.execute(
                        update(CEOSuggestedTask)
                        .where(CEOSuggestedTask.id == task.id)
                        .values(status='approved', created_task_id=p_id)
                    )
                    
                    await db_task.commit()
                    approved_count += 1
                    if approved_count % 10 == 0:
                        print(f"✅ {approved_count}/{len(tasks)} tamamlandi...")
                    
                except Exception:
                    print(f"❌ Gorev {task.id} hatasi:")
                    traceback.print_exc()
                    await db_task.rollback()

        print(f"🏁 SKOR: {approved_count}/{len(tasks)} basarili.")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(final_push())
