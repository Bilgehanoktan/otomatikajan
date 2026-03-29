
import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

async def verify_repair_api():
    print("--- Checking Repair API Endpoints ---")
    try:
        from core.repair_orchestrator import get_repair_orchestrator
        from repair.memory.incident_memory import incident_memory
        
        orch = get_repair_orchestrator()
        stats = orch.stats()
        print(f"[OK] Repair Stats: {stats}")
        
        incidents = list(incident_memory.list_open())
        print(f"[OK] Open Incidents count: {len(incidents)}")
        
        from api.repair_router import list_incidents
        # We can't easily call the route without a Request object, 
        # but we can verify the underlying memory.
        
    except Exception as e:
        print(f"[FAIL] Repair API verification failed: {e}")
        return False
    return True

async def verify_task_creation():
    print("\n--- Checking Task Creation Logic ---")
    try:
        from core.heal_engine import heal_engine
        score = heal_engine.system_health_score()
        print(f"[OK] System Health Score: {score}")
        
        if score < 0.35:
            print("[WARN] Health score is low (< 0.35). Task creation might be blocked by Circuit Breaker.")
        else:
            print("[OK] Health score is sufficient for task creation.")
            
    except Exception as e:
        print(f"[FAIL] Task logic verification failed: {e}")
        return False
    return True

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(verify_repair_api())
    success &= loop.run_until_complete(verify_task_creation())
    
    if success:
        print("\n[SUCCESS] Backend verification passed.")
    else:
        print("\n[FAILURE] Backend verification failed.")
        sys.exit(1)
