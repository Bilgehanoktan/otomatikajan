import asyncio
import os
from core.agi.learning.wisdom_synthesizer import WisdomSynthesizer
from core.agi.task_governance import SovereignGoal, GovernedTask, GovernanceStatus
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from db.session import AsyncSessionLocal
from db.models import Memory
from sqlalchemy import select, delete

async def test_saturation():
    print("--- Phase 60.6 Verification: Wisdom Saturation ---")
    synthesizer = WisdomSynthesizer()
    
    # 1. Cleanup old test wisdom
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Memory).where(Memory.agent_id == "wisdom_synthesizer"))
        await db.commit()
    
    # 2. Create a dummy task
    task = SovereignGoal(
        id="test-task-sat",
        title="Optimization of CSS rendering",
        description="Reducing layout shifts by pre-calculating viewport dimensions."
    )
    task.subtasks = [
        GovernedTask(id="st-1", agent_id="fe", prompt="fix css", status=GovernanceStatus.COMPLETED, result="layout fixed")
    ]
    
    # 3. First Synthesis (Should call LLM)
    print("\n[STEP 1] First Synthesis (LLM expected)...")
    # Note: This will actually call the LLM if configured, or use mock if we mock it.
    # For verification, we just want to ensure it SAVES a memory.
    res1 = await synthesizer.synthesize_from_task(task)
    print(f"Result 1: {res1}")
    
    # 4. Verify memory exists
    async with AsyncSessionLocal() as db:
        stmt = select(Memory).where(Memory.category == "semantic_wisdom")
        result = await db.execute(stmt)
        memories = result.scalars().all()
        print(f"Memories in DB: {len(memories)}")
        assert len(memories) >= 1
    
    # 5. Second Synthesis (Same Task -> Should be SATURATED)
    print("\n[STEP 2] Second Synthesis (Saturation expected)...")
    res2 = await synthesizer.synthesize_from_task(task)
    print(f"Result 2: {res2}")
    
    assert res2 == "SATURATED"
    print("✅ Success: LLM skipped for redundant pattern.")
    
    # 6. Verify importance increment
    async with AsyncSessionLocal() as db:
        stmt = select(Memory).where(Memory.category == "semantic_wisdom")
        result = await db.execute(stmt)
        memories = result.scalars().all()
        # Should still be 1 (didn't create a new one)
        assert len(memories) == 1
        print(f"Memory Importance: {memories[0].importance}")
        # Default save importance is 0.8 in synthesis code. 
        # _increment_importance adds 0.05.
        assert memories[0].importance > 0.8
    
    print("\n✅ Phase 60.6 Verification SUCCESS: Saturation threshold is active and preserving tokens.")

if __name__ == "__main__":
    asyncio.run(test_saturation())
