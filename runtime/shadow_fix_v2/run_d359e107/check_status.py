import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.orchestration.ceo.engine import get_ceo_engine
from libs.db.session import AsyncSessionLocal
from libs.db.models import CEOSuggestedTask
from sqlalchemy import select

async def check():
    print("Initializing CEO Engine...")
    ceo = get_ceo_engine()
    
    print("\n--- Direct Database Query ---")
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(CEOSuggestedTask))
        sugs = res.scalars().all()
        print(f"Direct Query - CEOSuggestedTask Count: {len(sugs)}")
        for s in sugs:
            print(f" - [{s.status}] {s.title} (ID: {s.id})")
            
    print("\n--- Calling get_findings() ---")
    res_findings = await ceo.get_findings()
    findings = res_findings.get("findings", [])
    print(f"get_findings() Count: {len(findings)}")
    for f in findings:
        print(f" - [{f['status']}] {f['finding']} (ID: {f['id']})")

if __name__ == "__main__":
    asyncio.run(check())
