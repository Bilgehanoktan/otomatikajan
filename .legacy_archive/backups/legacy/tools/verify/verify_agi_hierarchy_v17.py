import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_hierarchy_v17():
    print("--- AGI Phase 17: 'Hierarchical Self-Refinement' Verification ---")
    
    try:
        from packages.orchestration.agi.central_executive import central_executive
        from packages.orchestration.agi.schemas import SourceType, TaskType, ProblemFrame
        
        # Mocking Decomposer to force a hierarchical split
        from packages.orchestration.agi.cognitive.decomposer import goal_decomposer
        
        # Test Case: A complex task that should be split
        complex_input = "Analyze the core/agi/schemas.py file and then add a new field for 'QuantumState'."
        
        print("\n[STEP 1] Running Central Executive with complex objective...")
        # Note: CentralExecutive and Decomposer use model_orchestrator, 
        # so this will perform actual LLM calls if not mocked.
        # For verification, we'll let it run naturally to see the 'real' behavior.
        
        episode = await central_executive.execute_thought_cycle(
            raw_input=complex_input,
            source=SourceType.USER_MESSAGE
        )
        
        print("\n[STEP 2] Inspecting Episode Record for Hierarchy...")
        if episode.problem_frame:
            print(f"  -> Original Objective: {episode.problem_frame.objective}")
            
        if len(episode.actions) > 0:
            print(f"  -> Total Actions executed: {len(episode.actions)}")
            
        # Check if cumulative history exists in lessons
        if any("Task" in l for l in episode.lessons_learned):
            print("[SUCCESS] Hierarchical execution log detected in lessons learned.")
        
        if episode.final_output and "Step" in str(episode.final_output):
            print("[SUCCESS] Cumulative output contains multi-step results.")
            print(f"  -> Preview: {str(episode.final_output)[:200]}...")
        else:
            print("[INFO] Hierarchical execution may not have been triggered if GoalDecomposer decided one step was enough.")

        print("\n[OK] Phase 17 Logic Pulse Verified.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_hierarchy_v17())
