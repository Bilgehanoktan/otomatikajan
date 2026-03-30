import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_chronos_mesh():
    print("--- AGI 31.0 Verification ---")
    
    try:
        from core.agi.cognitive.chronos_mesh import chronos_mesh
        from core.agi.adaptation.timeline_selector import timeline_selector
        from llm.model_orchestrator import model_orchestrator
        
        print("[OK] AGI 31.0 components imported successfully.")
        
        # Mock LLM for Timeline Simulation
        mock_timelines = {
            "timelines": [
                {"type": "Conservative", "utility_score": 0.4, "risk_score": 0.1, "ethics_score": 1.0, "content": "Safe approach"},
                {"type": "Balanced", "utility_score": 0.7, "risk_score": 0.3, "ethics_score": 1.0, "content": "Mixed approach"},
                {"type": "Aggressive", "utility_score": 0.9, "risk_score": 0.8, "ethics_score": 0.9, "content": "Fast approach"}
            ]
        }
        model_orchestrator.generate_json = AsyncMock(return_value=mock_timelines)

        # 1. Test Chronos Mesh
        mock_plan = {"title": "Test Plan", "content": "Do something complex"}
        print("[INFO] Chronos Mesh: Simulating parallel futures...")
        timelines = await chronos_mesh.simulate_parallel_futures(mock_plan)
        
        if len(timelines) == 3:
            print(f"[OK] Chronos Mesh: Successfully simulated {len(timelines)} parallel timelines.")
        else:
            print(f"[ERROR] Chronos Mesh returned {len(timelines)} timelines instead of 3.")

        # 2. Test Timeline Selector
        print("[INFO] Timeline Selector: Selecting optimal timeline...")
        optimal = await timeline_selector.select_optimal_timeline(timelines)
        
        if optimal:
            print(f"[OK] Timeline Selector: Selected optimal future: {optimal.get('type')} (Score: {optimal.get('final_score')})")
            # Expected winner: Balanced usually (0.7*0.4 + 0.7*0.6 = 0.7) vs Conservative (0.4*0.4 + 0.9*0.6 = 0.7) 
            # Aggressive (0.9*0.4 + 0.2*0.6 = 0.36 + 0.12 = 0.48)
        else:
            print("[ERROR] Timeline Selector failed to select a future.")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_chronos_mesh())
