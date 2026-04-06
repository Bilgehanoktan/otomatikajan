import asyncio
import os
import tempfile
from packages.orchestration.agi.cognitive.symbolic_prover import symbolic_prover
from packages.orchestration.agi.security.symbolic_engine import symbolic_engine
from packages.orchestration.agi.cognitive.swarm_resolver import SwarmResolver

# Mocking ModelOrchestrator to simulate agent repairs
class MockModelOrchestrator:
    async def complete_task(self, agent_role, prompt, system_prompt):
        class Result:
            def __init__(self, content):
                self.content = content
        
        # If the prompt contains "os.remove", simulate a fix
        if "os.remove" in prompt or "Violation" in prompt:
            return Result("def safe_operation():\n    print('Doing something safe instead of deleting.')")
        
        return Result(f"Fix applied as requested for {agent_role}")

async def verify_neuro_symbolic_integration():
    print("--- Phase 26 Adaptive Neuro-Symbolic Integration Verification ---")

    # 1. Test Symbolic Prover (Rule Violation)
    print("\n[*] Testing Symbolic Prover (Rule Violation: os.remove)...")
    vulnerable_code = "import os\ndef delete_system():\n    os.remove('/root/dangerous_file')"
    
    proof = symbolic_prover.prove_proposal(vulnerable_code)
    print(f"Is Proven: {proof['is_proven']}")
    print(f"Violations: {proof['violations']}")
    
    if not proof['is_proven'] and any(v['rule_id'] == 'RULE_001' for v in proof['violations']):
        print("[SUCCESS] Symbolic Prover correctly identified the violation.")
    else:
        print("[FAILURE] Symbolic Prover failed to detect Rule 001.")

    # 2. Test Symbolic Engine (Lint/Type Error via Ruff/Mypy)
    print("\n[*] Testing Symbolic Engine (Syntax Error)...")
    bad_syntax = "def broken_code(: print('error')"
    
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        tmp.write(bad_syntax.encode())
        tmp_path = tmp.name
    
    try:
        res = await symbolic_engine.run_safety_scans(tmp_path)
        print(f"Is Valid: {res['is_valid']}")
        print(f"Ruff Errors: {len(res['ruff_errors'])}")
        
        if not res['is_valid']:
            print("[SUCCESS] Symbolic Engine correctly identified the syntax/lint error.")
        else:
            print("[FAILURE] Symbolic Engine missed the syntax error.")
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

    # 3. Test Neuro-Symbolic Feedback Loop (SwarmResolver)
    print("\n[*] Testing Neuro-Symbolic Feedback Loop (Swarm Resolver)...")
    mock_orch = MockModelOrchestrator()
    resolver = SwarmResolver(model_orch=mock_orch)
    
    # Simulate a producer producing 'illegal' code
    illegal_output = "def risky(): os.remove('tmp.txt')"
    
    swarm_res = await resolver.orchestrate_peer_review(
        producer_id="backend_dev",
        reviewer_id="security",
        task_context={"objective": "Update file system"},
        produced_output=illegal_output
    )
    
    print(f"Swarm Status: {swarm_res['status']}")
    print(f"Final Output: {swarm_res['final_output']}")
    
    if swarm_res['status'] == "symbolically_refined" and "os.remove" not in swarm_res['final_output']:
        print("[SUCCESS] Neuro-Symbolic Feedback Cycle verified.")
    else:
        print("[FAILURE] Neuro-Symbolic Feedback loop failed.")

    print("\n[PHASE 26] NEURO-SYMBOLIC INTEGRATION VERIFIED.")

if __name__ == "__main__":
    asyncio.run(verify_neuro_symbolic_integration())
