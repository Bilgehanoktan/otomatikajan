
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from services.orchestration.application.sovereign_cortex import SovereignCortex
from libs.db.session import AsyncSessionLocal, init_db
from libs.db.models.lineage_models import DecisionLineage
from sqlalchemy import select

async def run_drill():
    print("🚀 Starting Autonomous Evolution Drill...")
    
    # 1. Ensure DB is ready
    await init_db()
    
    # 2. Initialize Cortex
    cortex = SovereignCortex()
    
    # 3. Simulate an "Opportunity" if observer is too quiet
    # For this drill, we just trigger the loop
    print("🧠 Triggering self-evolution cycle...")
    # trigger_self_evolution is async and returns a summary or triggers background tasks
    # We call it directly to see if it executes without errors
    try:
        await cortex.trigger_self_evolution()
        print("✅ Evolution cycle triggered successfully.")
    except Exception as e:
        print(f"❌ Evolution cycle failed: {e}")
        return

    # 4. Check DecisionLineage for any new entries
    print("📊 Verifying Decision Lineage records...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DecisionLineage).order_by(DecisionLineage.created_at.desc()).limit(5)
        )
        decisions = result.scalars().all()
        
        if decisions:
            print(f"Found {len(decisions)} recent decisions:")
            for d in decisions:
                print(f" - [{d.created_at}] {d.decision_type} in {d.component_name}: {d.rationale[:50]}...")
        else:
            print("⚠️ No decisions found in lineage. (Loop might be running in background or no opportunities found)")

    print("\n🏁 Drill completed.")

if __name__ == "__main__":
    asyncio.run(run_drill())
