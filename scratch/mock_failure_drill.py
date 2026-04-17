import asyncio
from unittest.mock import MagicMock
from services.improve.evolution_orchestrator import AutonomousEvolutionOrchestrator
from libs.llm.model_orchestrator import ModelOrchestrator

async def run_drill():
    print("Starting Mock Failure Drill...")
    
    # Mock components
    mock_model = MagicMock(spec=ModelOrchestrator)
    project_root = "e:/ai_company_faz12.1"
    
    orchestrator = AutonomousEvolutionOrchestrator(mock_model, project_root)
    
    # Test file
    test_file = "libs/auth/critical_auth.py" # Protected path
    
    print(f"1. Testing Constitutional Guard for: {test_file}")
    is_locked = orchestrator.guard.is_locked(test_file)
    print(f"Result: {'LOCKED (Correct)' if is_locked else 'FAILED (Expected Locked)'}")
    
    print("\n2. Simulating Consecutive Failures for a non-protected file...")
    target = "libs/utils/minor_tweak.py"
    orchestrator.failure_counter[target] = 3  # Failed 3 times (Threshold met)
    
    print(f"Triggering STUCK T3 for {target}...")
    await orchestrator._diagnose_and_unstick(target, "Simulated recurring test failure")
    
    print(f"Check failure counter for {target}: {orchestrator.failure_counter[target]}")
    if orchestrator.failure_counter[target] == 999:
        print("SUCCESS: QUARANTINE ACTIVE")
    else:
        print("FAILURE: QUARANTINE NOT ACTIVE")

if __name__ == "__main__":
    asyncio.run(run_drill())
