import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from packages.persistence.session import AsyncSessionLocal
from packages.persistence.models.core_models import Project, ProjectStatus
from sqlalchemy import select
from apps.worker.tasks.celery_app import celery_app

async def enqueue_all():
    print("🚀 KUYRUK SENKRONIZASYONU...")
    async with AsyncSessionLocal() as db:
        stmt = select(Project).where(Project.status == ProjectStatus.QUEUED)
        res = await db.execute(stmt)
        projects = res.scalars().all()
        print(f"📦 {len(projects)} adet QUEUED projesi bulundu.")
        
        for p in projects:
            try:
                celery_app.send_task(
                    "tasks.project_tasks.run_project_task",
                    args=[str(p.id), p.title, p.description or "No description"],
                    kwargs={
                        "workflow_template": p.workflow_template or "default", 
                        "quality_profile": p.quality_profile or "production"
                    }
                )
                print(f"✅ Kuyruga eklendi: {p.id}")
            except Exception as e:
                print(f"❌ Hata ({p.id}): {e}")

if __name__ == "__main__":
    asyncio.run(enqueue_all())
