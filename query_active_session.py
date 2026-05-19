import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db.session import session_scope
from libs.db.models import CEOSuggestedTask, ImprovementOpportunity
from sqlalchemy import select

async def check():
    async with session_scope() as db:
        res_sug = await db.execute(select(CEOSuggestedTask))
        sugs = res_sug.scalars().all()
        print(f"CEOSuggestedTask Count in active session: {len(sugs)}")
        for s in sugs:
            print(f" - [{s.status}] {s.title} (ID: {s.id})")
            
        res_op = await db.execute(select(ImprovementOpportunity))
        ops = res_op.scalars().all()
        print(f"\nImprovementOpportunity Count in active session: {len(ops)}")
        # Print first 5
        for o in ops[:5]:
            print(f" - [{o.status}] {o.title} (ID: {o.id})")

if __name__ == "__main__":
    asyncio.run(check())
