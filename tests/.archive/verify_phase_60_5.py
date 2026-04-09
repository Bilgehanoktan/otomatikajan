import asyncio
import os
import json
from packages.orchestration.agi.monitoring.nervous_system import nervous_system
from packages.orchestration.agi.packages.quality_assurance.sovereign_evaluator import SovereignEvaluator
from packages.orchestration.agi.task_governance import GovernedTask, GovernanceStatus
from apps.api.routers.monitoring_router import monitoring_overview

async def verify_dashboard_metrics():
    print("--- Phase 60.5 Verification: Dashboard Metrics ---")
    
    # 1. Reset metrics
    nervous_system.cognitive_metrics["grounding_persistence"] = 1.0
    nervous_system.cognitive_metrics["dissonance_alerts"] = 0
    
    # 2. Simulate a Hallucinated Success (Score 0.2)
    print("\n[SCENARIO 1] Hallucinated Success Detection...")
    # Fix: Use correct GovernedTask fields
    fake_task = GovernedTask(
        id="test-hallucination-123",
        agent_id="test_agent",
        prompt="Delete a non-existent file",
        status=GovernanceStatus.COMPLETED
    )
    
    # Manually log a dissonance event
    nervous_system.log_grounding_event(0.2, True)
    
    print(f"Metrics after dissonance: {nervous_system.cognitive_metrics}")
    assert nervous_system.cognitive_metrics["dissonance_alerts"] == 1
    assert nervous_system.cognitive_metrics["grounding_persistence"] < 1.0
    
    # 3. Check API Exposure
    print("\n[SCENARIO 2] API Exposure Check...")
    class MockUser:
        pass
        
    result = await monitoring_overview(current_user=MockUser())
    agi_stats = result["agi"]
    
    print(f"API Output (AGI Section): {json.dumps(agi_stats, indent=2)}")
    
    assert agi_stats["grounding_score"] == nervous_system.cognitive_metrics["grounding_persistence"]
    assert agi_stats["dissonance_count"] == 1
    assert "Sovereign (v13.6-RC3)" in agi_stats["version"]
    
    print("\n[OK] Phase 60.5 Verification SUCCESS: Dashboard metrics are linked and exposed.")

if __name__ == "__main__":
    asyncio.run(verify_dashboard_metrics())
