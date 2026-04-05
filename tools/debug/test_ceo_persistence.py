
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from packages.orchestration.ceo_engine import CEOEngine
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.persistence.session import session_scope
from packages.persistence.models import ImprovementOpportunity
from sqlalchemy import select, func

async def test_persistence():
    print("Testing CEO Engine Persistence...")
    
    # Mock orchestrator
    orchestrator = ModelOrchestrator()
    ceo = CEOEngine(orchestrator)
    
    # 1. Run Scan
    print("Running CEO Scan...")
    results = await ceo.run_scan()
    print(f"Scan complete. Found {len(results)} results.")
    
    # 2. Verify DB
    async with session_scope() as db:
        res = await db.execute(select(func.count(ImprovementOpportunity.id)).where(ImprovementOpportunity.status == "open"))
        count = res.scalar()
        print(f"Double Check: ImprovementOpportunity table count (open): {count}")
        
        if count > 0:
            print("SUCCESS: Findings persisted to DB!")
        else:
            print("FAILURE: Findings NOT found in DB.")

if __name__ == "__main__":
    asyncio.run(test_persistence())
