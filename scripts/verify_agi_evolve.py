import asyncio
import os
import sys

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_evolution():
    print("--- AGI 12.2 Verification ---")
    
    try:
        from core.agi.orchestrator import agi_orchestrator
        from core.agi.world.repo_graph import repo_world_model
        from core.agi.learning.distiller import skill_distiller
        from core.agi.cognitive.simulator import simulation_engine
        
        print("[OK] All AGI components imported successfully.")
        
        # Test Repo Graph
        print("Taramayı test ediyor (Repo Graph)...")
        nodes = repo_world_model.scan()
        summary = repo_world_model.get_summary()
        print(f"[OK] Repo Graph summary: {summary}")
        
        # Test Orchestrator structure
        print(f"[OK] Orchestrator ready: {agi_orchestrator is not None}")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_evolution())
