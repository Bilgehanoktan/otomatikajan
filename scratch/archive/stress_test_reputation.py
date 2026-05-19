
import asyncio
import os
import sys

# Set path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from services.orchestration.trust_governor import trust_governor
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import AgentNode, AgentStatus
from sqlalchemy import select

async def run_stress_test():
    agent_name = "qa_engineer"
    print(f"--- Stress Test: Reputation System (Target: {agent_name}) ---")
    
    # 1. Initial State
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(AgentNode).where(AgentNode.name == agent_name))
        agent = res.scalar_one()
        print(f"Initial Score: {agent.trust_score:.2f}, Status: {agent.status}")

    # 2. Simulate 5 Failures
    for i in range(1, 6):
        print(f"\nStep {i}: Recording FAILURE for {agent_name}...")
        await trust_governor.record_agent_outcome(agent_name, success=False)
        
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(AgentNode).where(AgentNode.name == agent_name))
            agent = res.scalar_one()
            print(f"Current Score: {agent.trust_score:.2f}, Status: {agent.status}")
            if agent.status == AgentStatus.QUARANTINED:
                print(f"SUCCESS: Agent {agent_name} has been QUARANTINED.")
                break

    # 3. Verify Re-allocation failure (Optional check)
    print("\n--- Testing Recovery: Recording SUCCESS for quarantined agent ---")
    await trust_governor.record_agent_outcome(agent_name, success=True)
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(AgentNode).where(AgentNode.name == agent_name))
        agent = res.scalar_one()
        print(f"Final Score: {agent.trust_score:.2f}, Status: {agent.status}")
        print("Note: Quarantined agents should stay quarantined even if score improves, until manually released (governance policy).")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
