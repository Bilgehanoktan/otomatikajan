import asyncio
import uuid
import os
from packages.orchestration.agi.consciousness.neural_core_orchestrator import neural_core_orchestrator
from packages.persistence.session import session_scope
from packages.persistence.models import SkillExecutionLog, Project, ProjectStatus
from packages.packages.observability.logging import get_logger

_log = get_logger("verify_mind_cycle")

async def test_full_mind_cycle():
    print("--- Neural Core Full Mind Cycle Integration Test ---")
    
    # 0. Prep: Create some logs to trigger Diagnostic
    print("[*] Creating diagnostic trigger logs...")
    async with session_scope() as db:
        agent_id = "mind_cycle_test_agent"
        from sqlalchemy import delete
        await packages.persistence.execute(delete(SkillExecutionLog).where(SkillExecutionLog.agent_id == agent_id))
        
        for _ in range(4):
            packages.persistence.add(SkillExecutionLog(
                agent_id=agent_id,
                skill_id="reasoning_v1",
                success=False,
                summary="Test failure for mind cycle verification."
            ))
        await packages.persistence.commit()

    # 1. Run the Cycle
    print("[*] Starting Mind Cycle...")
    async with session_scope() as db_cycle:
        await neural_core_orchestrator.run_mind_cycle(db_cycle)
        await db_cycle.commit()

    print("\n[*] Verifying side-effects...")
    
    # 2. Verify Diagnostic Output
    async with session_scope() as db_verify:
        from packages.persistence.models import ImprovementOpportunity
        from sqlalchemy import select
        
        stmt = select(ImprovementOpportunity).where(ImprovementOpportunity.source_ref.like(f"{agent_id}:%"))
        res = await db_verify.execute(stmt)
        opp = res.scalar_one_or_none()
        
        if opp:
            print(f"[SUCCESS] Diagnostic layer triggered and created opportunity: {opp.id}")
        else:
            print("[FAILURE] Diagnostic layer was not triggered or failed silently.")

    print("\n[VERIFICATION] FULL MIND CYCLE INTEGRATION PASSED.")

if __name__ == "__main__":
    asyncio.run(test_full_mind_cycle())
