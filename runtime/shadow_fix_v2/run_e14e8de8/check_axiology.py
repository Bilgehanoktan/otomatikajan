
import asyncio
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SovereignEvidence
from sqlalchemy import select

async def check_axiology():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(SovereignEvidence).where(SovereignEvidence.evidence_type == "axiology_audit"))
        records = res.scalars().all()
        for r in records:
            print(f"ID: {r.id}")
            print(f"Evidence Type: {r.evidence_type}")
            print(f"Content: {r.content}")
            print(f"Metadata: {r.meta_data}")
            print(f"Created At: {r.created_at}")

if __name__ == "__main__":
    asyncio.run(check_axiology())
