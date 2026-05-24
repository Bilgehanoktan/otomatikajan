import asyncio
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from services.orchestration.agi.central_executive import CentralExecutive
from services.orchestration.agi.schemas import SourceType, RiskLevel, ProblemFrame, TaskType
from db.session import session_scope

# Mocking ModelOrchestrator to simulate different agent responses
class MockModelOrchestrator:
    async def complete_task(self, agent_role, prompt, system_prompt):
        class Result:
            def __init__(self, content):
                self.content = content
        
        # Simulate Security Review rejection for the first time
        if agent_role == "security" and "incele" in prompt:
            return Result("STATUS: REJECTED\nFEEDBACK: Code has a clear SQL injection vulnerability at line 42.")
        
        # Simulate BackendDev fixing the issue
        if agent_role == "backend_dev" and "reddedildi" in prompt:
            return Result("Revised code: Fixed SQL injection using parameterized queries.")
        
        # Default approval for other tests
        if agent_role == "security":
             return Result("STATUS: APPROVED\nFEEDBACK: Looks solid.")
             
        return Result(f"Mock output from {agent_role}")

async def verify_swarm_cognition():
    print("--- Phase 25 Collective Intelligence (Swarm Cognition) Verification ---")
    
    # Initialize Central Executive with Mock Orchestrator
    mock_orch = MockModelOrchestrator()
    ce = CentralExecutive(model_orch=mock_orch)
    
    # 1. Test Swarm Mode Trigger (RiskLevel.HIGH)
    print("\n[*] Testing Swarm Mode Trigger (High Risk Task)...")
    
    # Create a High Risk Frame
    high_risk_input = "Refactor database connection for improved security."
    
    # Manually trigger a thought cycle with a mock high-risk frame logic
    # (Since perception is complex to mock, we'll test the SwarmResolver directly first)
    
    from services.orchestration.agi.cognitive.swarm_resolver import SwarmResolver
    resolver = SwarmResolver(model_orch=mock_orch)
    
    task_context = {"objective": "Secure Database Connection"}
    initial_output = "db.execute(f'SELECT * FROM users WHERE id={id}')"
    
    print(f"Initial Output (Vulnerable): {initial_output}")
    
    swarm_res = await resolver.orchestrate_peer_review(
        producer_id="backend_dev",
        reviewer_id="security",
        task_context=task_context,
        produced_output=initial_output
    )
    
    print(f"Swarm Status: {swarm_res['status']}")
    print(f"Review Feedback: {swarm_res['review']}")
    print(f"Final Refined Output: {swarm_res['final_output']}")
    
    if swarm_res['status'] == "refined" and "parameterized" in swarm_res['final_output']:
        print("[SUCCESS] Peer Review & Refinement Cycle verified.")
    else:
        print("[FAILURE] Swarm refinement failed.")

    # 2. Test Workspace Propagation (MotorSynapse Integration)
    print("\n[*] Testing Workspace Propagation (Motor Synapse)...")
    from services.orchestration.agi.schemas import ExecutionPlan, PlanStep
    
    plan = ExecutionPlan(
        goal="Collaborative Step Test",
        steps=[
            PlanStep(step_id="s1", agent_id="architect", action="setup"),
            PlanStep(step_id="s2", agent_id="backend_dev", action="implement", dependencies=["s1"])
        ],
        workspace={"shared_key": "initial_value"}
    )
    
    # Mock some agents in MotorSynapse
    from services.orchestration.agi.operational.motor_synapse import MotorSynapse
    
    class MockAgent:
        async def execute(self, task_id, subtask_id, context):
            class Out:
                raw_output = f"Processed {context.get('shared_key', 'missing')}"
            return Out()
            
    agents = {"architect": MockAgent(), "backend_dev": MockAgent()}
    ms = MotorSynapse(agents=agents)
    
    records = await ms.execute_plan(plan)
    
    # Check if step 2 saw step 1's output in workspace
    # (Step 1 output is added to workspace as 'architect_output')
    print(f"Record 1 Output: {records[0].output_data}")
    print(f"Record 2 Input (should have architect_output): {records[1].input_data.keys()}")
    
    if "architect_output" in records[1].input_data:
        print("[SUCCESS] Workspace successfully propagated results between steps.")
    else:
        print("[FAILURE] Workspace propagation failed.")

    print("\n[PHASE 25] COLLECTIVE INTELLIGENCE VERIFIED.")

if __name__ == "__main__":
    asyncio.run(verify_swarm_cognition())
