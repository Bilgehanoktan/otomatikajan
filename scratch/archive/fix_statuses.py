import asyncio
import sys
import os
sys.path.insert(0, '.')

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, SubTask, ProjectStatus
from sqlalchemy import select, update

async def main():
    async with AsyncSessionLocal() as db:
        # 1. Fix Projects
        res = await db.execute(select(Project))
        projects = res.scalars().all()
        fixed_p = 0
        for p in projects:
            # We check the raw value in the DB by bypassing the enum if possible, 
            # but since we already got a LookupError in the other script, 
            # we know some are 'failed'.
            pass
            
        # Use raw SQL to be safe from Enum lookup errors during loading
        from sqlalchemy import text
        
        # Normalize Projects
        res_p = await db.execute(text("UPDATE projects SET status = UPPER(status)"))
        print(f"Projects updated: {res_p.rowcount}")
        
        # Normalize SubTasks
        res_st = await db.execute(text("UPDATE subtasks SET status = UPPER(status)"))
        print(f"SubTasks updated: {res_st.rowcount}")
        
        # Also handle common mismatches
        await db.execute(text("UPDATE projects SET status = 'FAILED' WHERE status = 'ERROR'"))
        await db.execute(text("UPDATE subtasks SET status = 'FAILED' WHERE status = 'ERROR'"))
        
        await db.commit()
        print("Database normalization complete.")

if __name__ == "__main__":
    asyncio.run(main())
