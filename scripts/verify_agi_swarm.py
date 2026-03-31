import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_swarm_intelligence():
    print("--- AGI 23.0 Verification ---")
    
    try:
        from core.agi.cognitive.swarm_cortex import swarm_cortex
        from core.agi.operational.swarm_orchestrator import swarm_orchestrator
        
        print("[OK] AGI 23.0 components imported successfully.")
        
        # 1. Test Swarm Cortex
        await swarm_cortex.register_unit("test_unit_A", ["coding", "testing"])
        await swarm_cortex.update_hive_context("Testing Swarm Integration")
        
        state = swarm_cortex.shared_state
        if "test_unit_A" in [u["id"] for u in state["active_units"]]:
            print(f"[OK] Swarm Cortex: Unit registration successful.")
        else:
            print("[ERROR] Hive Memory: Unit registration failed.")

        if state["global_context"] == "Testing Swarm Integration":
            print(f"[OK] Swarm Cortex: Context synchronization successful.")
        else:
            print("[ERROR] Hive Memory: Context synchronization failed.")

        # 2. Test Swarm Orchestrator
        result = await swarm_orchestrator.execute_swarm_task("Build a distributed AGI node")
        
        if result.get("status") == "completed":
            print(f"[OK] Swarm Orchestrator: Task execution successful.")
            print(f"    - Synthesis: {result['synthesis']}")
            print(f"    - Units involved: {result['units_involved']}")
        else:
            print(f"[ERROR] Swarm Orchestrator failed: {result}")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_swarm_intelligence())
