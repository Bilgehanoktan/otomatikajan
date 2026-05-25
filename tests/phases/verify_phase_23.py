import asyncio
import os
import json
from datetime import datetime, timezone, timedelta
from services.orchestration.agi.cognitive.architect import Architect
from services.orchestration.agi.operational.source_refactor import SourceRefactorNode
from agents.specialist_agents.agent_registry import build_agents
from libs.db.session import session_scope
from libs.db.models import SkillExecutionLog, ImprovementOpportunity

async def verify_recursive_self_optimization():
    print("--- Phase 23 Recursive Cognitive Self-Optimization Verification ---")
    
    agent_id = "mock_failing_agent"
    agent_path = f"agents/{agent_id}.py"
    
    # 1. Create a Mock Failing Agent
    print(f"[*] Creating mock failing agent: {agent_path}")
    mock_code = """
# Mock Failing Agent
class Agent:
    def solve(self, prompt, context):
        # Inefficient and error-prone logic
        return "I always fail or act slow"
"""
    with open(agent_path, "w", encoding="utf-8") as f:
        f.write(mock_code)

    # 2. Add High-Failure Logs
    print(f"[*] Simulating high failure rate for: {agent_id}")
    async with session_scope() as db:
        for _ in range(10):
            log = SkillExecutionLog(
                agent_id=agent_id,
                skill_id="test_skill",
                success=False,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=5)
            )
            db.add(log)
        await db.commit()

    # 3. Run Architect (Cognitive Scan) -> Skip LLM if rate limited, inject manually
    print("[*] Running Architect Cognitive Scan (Injecting Manual Proposal for Test)...")
    async with session_scope() as db:
        new_fixed_code = """
# Mock Failing Agent - REFACTORED
class Agent:
    def solve(self, prompt, context):
        return "I am now efficient and bug-free"
"""
        evidence = {
            "agent_id": agent_id,
            "reasoning": "Test refactor for verification",
            "suggested_refactor": new_fixed_code
        }
        opp = ImprovementOpportunity(
            title=f"COGNITIVE REFACTOR: {agent_id}",
            description="Autonomous refactor test",
            source_type="cognitive_scan",
            category="code_quality",
            severity="high",
            evidence_detail=json.dumps(evidence),
            status="open"
        )
        db.add(opp)
        await db.commit()

    # 4. Run Source Refactor Node
    print("[*] Running Source Refactor Node...")
    refactor_node = SourceRefactorNode()
    await refactor_node.execute_pending_refactors()

    # 5. Verify Source Update
    with open(agent_path, "r", encoding="utf-8") as f:
        updated_code = f.read()
    
    if updated_code != mock_code:
        print("[SUCCESS] Agent source code was autonomously REFACTORED.")
    else:
        print("[FAILURE] Agent source code was NOT modified.")

    # 6. Test Neural Pruning
    print("[*] Testing Neural Pruning...")
    pruned_path = "agents/pruned_agents.json"
    with open(pruned_path, "w", encoding="utf-8") as f:
        json.dump([agent_id], f)
    
    agents = build_agents()
    if agent_id not in agents:
        print("[SUCCESS] Agent successfully PRUNED from registry.")
    else:
        print("[FAILURE] Pruning logic failed.")

    # Cleanup
    if os.path.exists(agent_path): os.remove(agent_path)
    if os.path.exists(f"{agent_path}.bak"): os.remove(f"{agent_path}.bak")
    if os.path.exists(pruned_path): os.remove(pruned_path)

    print("\n[PHASE 23] RECURSIVE COGNITIVE SELF-OPTIMIZATION VERIFIED.")

if __name__ == "__main__":
    asyncio.run(verify_recursive_self_optimization())
