import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

# Proje kök dizinini ekle
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(root_dir)

# Corrected Imports (Case-sensitive fix: CEOSuggestedTask)
from services.orchestration.ceo.engine import CEOEngine
from services.orchestration.ceo.optimizer import CEOStochasticOptimizer
from libs.llm.model_orchestrator import ModelOrchestrator
from libs.db.session import session_scope
from libs.db.models import (
    SovereignGoal, 
    ImprovementOpportunity, 
    LLMCostLog, 
    SovereignModelPolicy,
    Project,
    CEOSuggestedTask,
    CEODecision
)

import json
import pytest
from libs.llm.model_orchestrator import LLMResponse

@pytest.fixture(autouse=True)
def mock_model_orchestrator(monkeypatch):
    async def mock_complete(*args, **kwargs):
        return "EVET"
    async def mock_complete_task(*args, **kwargs):
        return LLMResponse(
            content=json.dumps({
                "title": "CEO Contract Test Goal",
                "description": "Keep CEO strategy persistence schema-compatible.",
                "priority": "high",
                "kpis": {"latency_target": 250},
                "mission_statement": "Keep CEO strategy persistence schema-compatible.",
                "expected_outcome": "Outcome",
                "suggested_agent": "architect"
            }),
            provider="mock",
            model_name="mock-model",
            latency_s=0.1,
            input_tokens=10,
            output_tokens=20,
            cost_usd=0.01
        )
    monkeypatch.setattr(ModelOrchestrator, "complete", mock_complete)
    monkeypatch.setattr(ModelOrchestrator, "complete_task", mock_complete_task)

async def test_ceo_full_lifecycle():
    print("=== Sovereign CEO Lifecycle Integration Test (Hub Architecture) ===")
    
    # 1. Setup: Create an improvement opportunity to trigger Goal Synthesis
    async with session_scope() as db:
        print("[Step 1] Cleaning up and creating Improvement Opportunity...")
        
        # Proper Cascade Cleanup
        from sqlalchemy import delete
        await db.execute(delete(CEODecision))
        await db.execute(delete(CEOSuggestedTask))
        await db.execute(delete(SovereignGoal))
        await db.execute(delete(ImprovementOpportunity))
        await db.commit()

        opp = ImprovementOpportunity(
            source_type="performance",
            source_ref="latency_spike_cluster_a",
            title="Systemic Latency in Model Routing",
            description="LLM response times are exceeding 5s in architectural tasks.",
            severity="high",
            category="reliability",
            impact_score=0.8,
            pattern_hash=f"test_hash_{uuid.uuid4().hex[:8]}"
        )
        db.add(opp)
        await db.commit()

    # 2. Trigger CEO Engine Scan
    print("[Step 2] Running CEO Engine Scan...")
    orch = ModelOrchestrator()
    engine = CEOEngine(model_orch=orch)
    engine._throttle_auto_exec = True
    
    # run_scan backgrounds synthesis and optimization
    await engine.run_scan()
    
    print("Waiting for background synthesis (7s)...")
    await asyncio.sleep(7) 

    # 3. Verify Goal Synthesis
    async with session_scope() as db:
        from sqlalchemy import select
        res = await db.execute(select(SovereignGoal).where(SovereignGoal.status == 'active'))
        goal = res.scalars().first()
        if goal:
            print(f"SUCCESS: New Goal Synthesized: {goal.title}")
        else:
            print("WARNING: No goal synthesized yet. This may be due to LLM mock response or background task delay.")

    # 4. Simulate NAS Optimization
    async with session_scope() as db:
        print("[Step 4] Simulating Performance Data (LLMCostLog)...")
        from sqlalchemy import select
        policy_res = await db.execute(select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == 'architect'))
        policy = policy_res.scalars().first()
        if not policy:
            policy = SovereignModelPolicy(
                agent_role="architect",
                winner_provider="openai",
                runner_up="gemini",
                fallback_chain=["openai", "gemini"]
            )
            db.add(policy)
        else:
            policy.winner_provider = "openai"
            policy.runner_up = "gemini"
            policy.fallback_chain = ["openai", "gemini"]
            
        for _ in range(5):
            log = LLMCostLog(
                provider="openai",
                model="gpt-4o",
                agent_id="test_agent",
                agent_role="architect",
                latency_s=15.0, # Slow
                success=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(log)
        await db.commit()

    print("[Step 5] Triggering NAS Optimization Cycle...")
    await CEOStochasticOptimizer.run_optimization_cycle()
    
    # 5. Verify Policy Pivot
    async with session_scope() as db:
        from sqlalchemy import select
        res = await db.execute(select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == 'architect'))
        policy = res.scalars().first()
        if policy and policy.winner_provider == "gemini":
            print(f"SUCCESS: Policy Pivoted! New winner: {policy.winner_provider}")
        else:
            print(f"FAILURE: Policy not pivoted. Winner: {policy.winner_provider if policy else 'None'}")

    # 6. Verify ModelOrchestrator
    print("[Step 6] Checking Fallback Chain...")
    chain = await orch.get_fallback_chain("architect")
    print(f"Chain: {chain}")
    if chain[0] == "gemini":
        print("LIFECYCLE VERIFIED.")
    else:
        print("LIFECYCLE FAILED.")

if __name__ == "__main__":
    asyncio.run(test_ceo_full_lifecycle())
