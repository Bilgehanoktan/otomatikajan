import asyncio
import os
import sys

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_consensus_and_decomposition():
    print("--- AGI 12.8 & 12.9 Verification ---")
    
    try:
        from packages.orchestration.agi.cognitive.consensus_manager import consensus_manager
        from packages.orchestration.agi.cognitive.decomposer import goal_decomposer
        from packages.orchestration.agi.orchestrator import agi_orchestrator
        from packages.orchestration.agi.schemas import ProblemFrame, TaskType, RiskLevel, ExecutionPlan
        
        print("[OK] AGI 12.8/12.9 components imported successfully.")
        
        # Test Decomposer Presence
        frame = ProblemFrame(task_type=TaskType.FIX, objective="Complex Refactoring", priority=9)
        sub_tasks = await goal_decomposer.break_down(frame)
        print(f"[OK] Goal Decomposer: {len(sub_tasks)} tasks identified.")
        
        # Test Consensus Manager Presence
        print(f"[OK] Consensus Manager ready for resolution.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_consensus_and_decomposition())
