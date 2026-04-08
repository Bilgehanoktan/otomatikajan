import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append("e:/ai_company_faz12.1")

from packages.persistence.session import AsyncSessionLocal, init_db
from packages.persistence.models import Memory

async def record_shift():
    await init_db()
    async with AsyncSessionLocal() as db:
        m = Memory(
            agent_id='system',
            category='evolution_event',
            body='Phase 41-45: Sovereign Transition (v45.0) initiated. Components: sovereign_evolution_45, subconscious_cortex_45.',
            metadata_={
                'from_version': '40.0',
                'to_version': '45.0',
                'status': 'initiated',
                'provenance': 'User instruction for autonomous evolution & renaming.'
            },
            importance=1.0
        )
        packages.persistence.add(m)
        await packages.persistence.commit()
        print("SUCCESS: VERSION_SHIFT_45_RECORDED")

if __name__ == "__main__":
    asyncio.run(record_shift())
