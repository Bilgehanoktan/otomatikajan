import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.orchestration.ceo.engine import get_ceo_engine
from libs.db.session import AsyncSessionLocal
from libs.db.models import CEOSuggestedTask, Project
from sqlalchemy import select

async def trigger():
    print("Initializing CEO Engine...")
    ceo = get_ceo_engine()
    
    print("\n--- Triggering run_scan() ---")
    try:
        await ceo.run_scan()
        print("Scan completed successfully!")
    except Exception as e:
        print(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Querying Suggested Tasks & Generated Projects ---")
    async with AsyncSessionLocal() as db:
        res_sugs = await db.execute(select(CEOSuggestedTask))
        sugs = res_sugs.scalars().all()
        print(f"Total CEOSuggestedTask in DB: {len(sugs)}")
        for s in sugs:
            print(f" - [{s.status}] Sug ID: {s.id} | Title: {s.title} | Created Project ID: {s.created_task_id}")
            
        res_projs = await db.execute(select(Project).where(Project.ceo_managed == True))
        projs = res_projs.scalars().all()
        print(f"\nTotal CEO-Managed Projects in DB: {len(projs)}")
        for p in projs:
            print(f" - [{p.status}] Project ID: {p.id} | Title: {p.title} | Progress: {p.progress_pct}%")

if __name__ == "__main__":
    asyncio.run(trigger())
