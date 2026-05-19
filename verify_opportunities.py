import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db.session import AsyncSessionLocal, is_db_degraded, db_error
from libs.db.models.core_models import ImprovementOpportunity, CEOSuggestedTask, Project
from sqlalchemy import select, func

async def check():
    print("=== Database Connection Status ===")
    print(f"Is Degraded (SQLite Fallback): {is_db_degraded()}")
    print(f"DB Error: {db_error()}")
    
    async with AsyncSessionLocal() as db:
        try:
            opp_count = await db.scalar(select(func.count(ImprovementOpportunity.id)))
            print(f"ImprovementOpportunities (Total Count): {opp_count}")
            
            res_opps = await db.execute(select(ImprovementOpportunity))
            opps = res_opps.scalars().all()
            for o in opps:
                print(f" - [{o.status}] Opp ID: {o.id} | Title: {o.title} | Severity: {o.severity} | Score: {o.priority_score}")
        except Exception as e:
            print(f"Error checking ImprovementOpportunity: {e}")
            
        try:
            sug_count = await db.scalar(select(func.count(CEOSuggestedTask.id)))
            print(f"CEOSuggestedTasks (Total Count): {sug_count}")
            
            res_sugs = await db.execute(select(CEOSuggestedTask))
            sugs = res_sugs.scalars().all()
            for s in sugs:
                print(f" - [{s.status}] Sug ID: {s.id} | Title: {s.title} | Priority: {s.priority}")
        except Exception as e:
            print(f"Error checking CEOSuggestedTask: {e}")
            
        try:
            proj_count = await db.scalar(select(func.count(Project.id)))
            print(f"Projects (Total Count): {proj_count}")
            res_projs = await db.execute(select(Project))
            projs = res_projs.scalars().all()
            for p in projs:
                print(f" - [{p.status}] Project: {p.title} | Progress: {p.progress_pct}%")
        except Exception as e:
            print(f"Error checking Projects: {e}")

if __name__ == "__main__":
    asyncio.run(check())
