import asyncio
import uuid
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.governance_models import PolicyProposal
from datetime import datetime, timezone

async def register_hardening():
    async with AsyncSessionLocal() as db:
        prop = PolicyProposal(
            id=uuid.uuid4(),
            title="SOV-RES-01: API Resilience Hardening",
            description="Implemented Auto-Retry and Offline Fallback for UI-Backend communication.",
            scope="OPS",
            proposed_changes={"action": "hardening", "protocol": "SOV-RES-01"},
            status="COMMITTED",
            author_id="ANTIGRAVITY",
            created_at=datetime.now(timezone.utc)
        )
        db.add(prop)
        await db.commit()
        print("Hardening mühürlendi (Governance Ledger).")

if __name__ == "__main__":
    asyncio.run(register_hardening())
