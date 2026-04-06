import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from packages.orchestration.agi.central_executive import CentralExecutive
from packages.orchestration.agi.schemas import SourceType, TaskType, RiskLevel, ProblemFrame, ContextPackage

@pytest.mark.asyncio
async def test_state_aware_degraded_planning():
    """
    Sistemin 'degraded' (kısıtlı) moddayken nasıl karar verdiğini test eder.
    """
    # 1. Mock ModelOrchestrator to simulate degraded health
    mock_orch = AsyncMock()
    mock_orch.get_health_score.return_value = 0.5 # < 0.7 interpreted as degraded
    mock_orch.circuit_breaker_tripped = False
    
    # 2. Mock 'complete' to return multi-plan variants
    # Variant 1: Aggressive (Write deep)
    # Variant 2: Safe (Read only/Small fix)
    variants = [
        {
            "goal": "Deep Fix",
            "steps": [{"step_id": "s1", "agent_id": "architect", "action": "rewrite_all"}],
            "estimated_risk": "high"
        },
        {
            "goal": "Safe Fix",
            "steps": [{"step_id": "s1", "agent_id": "architect", "action": "minimal_patch"}],
            "estimated_risk": "low"
        }
    ]
    mock_orch.complete.return_value = json.dumps(variants)
    
    # 3. Mock ForesightCortex to score the variants
    # Variant 1 (Deep Fix) will have many predicted risks and low alignment in degraded mode
    # Variant 2 (Safe Fix) will have high alignment
    with patch("packages.orchestration.agi.cognitive.strategic_decision_center.foresight_cortex.simulate_plan", new_callable=AsyncMock) as mock_sim:
        mock_sim.side_effect = [
            {"predicted_risks": [{"step": 1, "severity": "high"}], "strategic_alignment_score": 0.2}, # For Deep Fix
            {"predicted_risks": [], "strategic_alignment_score": 0.95}  # For Safe Fix
        ]
        
        ce = CentralExecutive(model_orch=mock_orch)
        
        # Test input
        frame = ProblemFrame(task_type=TaskType.FIX, objective="Fix potential memory leak", risk_level=RiskLevel.MEDIUM)
        
        # We'll use a manually injected context for direct testing of Decision Center
        context = ContextPackage(working_context="Task description", integrity_status={"mode": "degraded"})
        
        plan = await ce.decision.decide(frame, context)
        
        # Assertions
        assert plan.goal == "Safe Fix"
        assert plan.estimated_risk == RiskLevel.LOW
        assert len(plan.evaluated_alternatives) == 2
        print(f"Strategic Decision: SUCCESS. Picked '{plan.goal}' with risk {plan.estimated_risk.value}")

if __name__ == "__main__":
    asyncio.run(test_state_aware_degraded_planning())
