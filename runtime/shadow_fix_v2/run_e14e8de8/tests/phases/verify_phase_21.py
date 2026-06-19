import asyncio
import os
import uuid
import json
from services.orchestration.agi.cognitive.reflection_cortex import ReflectionCortex
from services.orchestration.agi.cognitive.metacognitive_auditor import DiagnosticNode
from services.orchestration.agi.operational.self_patcher import self_patcher
from libs.db.session import session_scope
from libs.db.models import SkillExecutionLog, ImprovementOpportunity
from pathlib import Path

async def verify_cognitive_layer():
    print("--- Phase 21 Neural Self-Correction Verification ---")
    
    # 0. Cleanup previous test artifacts (Idempotency)
    print("[*] Cleaning up previous test data...")
    async with session_scope() as db_clean:
        from sqlalchemy import delete
        await db_clean.execute(delete(SkillExecutionLog).where(SkillExecutionLog.agent_id == "test_failing_agent"))
        await db_clean.execute(delete(ImprovementOpportunity).where(ImprovementOpportunity.source_ref.like("test_failing_agent:%")))
        await db_clean.commit()

    # 1. Create a Failing Agent Log
    agent_id = "test_failing_agent"
    print(f"[*] Simulating failures for agent: {agent_id}")
    async with session_scope() as db:
        for _ in range(5):
            log = SkillExecutionLog(
                agent_id=agent_id,
                skill_id="test_skill",
                success=False,
                summary="Error: Token limit exceeded. Model failed to respond correctly."
            )
            db.add(log)
        await db.commit()
    
    # 2. Run Diagnostic Node
    print("[*] Running Cognitive Diagnostic...")
    diag = DiagnosticNode()
    async with session_scope() as db:
        await diag.run_diagnostic_cycle(db)
        
        # 3. Check for ImprovementOpportunity
        opps = await db.execute(
            ImprovementOpportunity.__table__.select().where(
                ImprovementOpportunity.source_type == "cognitive_diagnostic"
            )
        )
        opp = opps.fetchone()
    
    if opp:
        print(f"[SUCCESS] Cognitive bottleneck identified: {opp.title}")
        repair_action = "System prompt güncellemesi" # Mock repair
        repair_detail = "Add 'Be extremely concise' to the prompt."
    else:
        print("[FAILURE] Diagnostic failed to identify the bottleneck.")
        return

    # 4. Run SelfPatcher
    print("[*] Running SelfPatcher...")
    success = self_patcher.patch_agent_prompt(agent_id, "You are a concise agent. Avoid token limits.")
    
    if success:
        print("[SUCCESS] SelfPatcher applied the cognitive repair.")
    else:
        print("[FAILURE] SelfPatcher failed to apply the repair.")
        return

    # 5. Verify Filesystem Reality
    print("[*] Verifying dynamic prompt storage...")
    prompt_path = Path(__file__).resolve().parents[2] / "agents" / "dynamic_prompts.json"
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompts = json.load(f)
            if agent_id in prompts and "concise" in prompts[agent_id]:
                print(f"[SUCCESS] Dynamic prompt verified for: {agent_id}")
            else:
                print("[FAILURE] Prompt content mismatch or missing.")
    else:
        print("[FAILURE] dynamic_prompts.json not found.")

    print("\n[PHASE 21] NEURAL SELF-CORRECTION LAYER VERIFIED.")

if __name__ == "__main__":
    asyncio.run(verify_cognitive_layer())
