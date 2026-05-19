
import asyncio
import uuid
import sys
import os
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def check_incidents():
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import OperationalIncident
    from sqlalchemy import select, desc
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(OperationalIncident).order_by(desc(OperationalIncident.created_at)).limit(10))
        incidents = res.scalars().all()
        
        print(f"--- SON 10 OLAY ({len(incidents)}) ---")
        for i in incidents:
            print(f"ID: {i.id}")
            print(f"TİP: {i.incident_type}")
            print(f"MESAJ: {i.message}")
            print(f"PAYLOAD: {i.payload}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_incidents())
