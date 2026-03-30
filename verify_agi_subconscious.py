import asyncio
import os
import sys
from datetime import datetime

# Workspace root'u sys.path'e ekle
sys.path.append(os.getcwd())

async def verify_nexus_quantum_sync():
    print(f"[{datetime.now().isoformat()}] Phase 17 Cognitive Verification Started...")
    
    # 1. Singleton Sync Check
    try:
        from core.agi.cognitive.nexus_orchestrator import nexus_orchestrator
        from core.context import orchestrator as context_orch
        
        print("[-] Checking Singleton Integrity...")
        if context_orch is nexus_orchestrator:
            print("[OK] Global context.orchestrator is linked to Nexus.")
        else:
            print("[FAIL] Global context.orchestrator is NOT linked to Nexus.")
            return False
            
    except Exception as e:
        print(f"[FAIL] Singleton Import Error: {e}")
        return False
        
    # 2. Nexus goal coordination check
    try:
        print("[-] Testing Nexus Goal Coordination (Dry-Run)...")
        # coordinate_goal normally triggers agents, we check if the method exists and is callable
        if hasattr(nexus_orchestrator, "coordinate_goal"):
            print("[OK] NexusOrchestrator has coordinate_goal method.")
        else:
            print("[FAIL] NexusOrchestrator missing coordinate_goal.")
            return False
            
        # Legacy compatibility check
        if hasattr(nexus_orchestrator, "run_project"):
            print("[OK] NexusOrchestrator has legacy run_project compatibility.")
    except Exception as e:
        print(f"[FAIL] Nexus Coordination Check Error: {e}")
        return False
        
    # 3. Quantum Executor Simulation Check
    try:
        from core.agi.operational.quantum_executor import quantum_executor
        print("[-] Testing Quantum Executor 'Look-Ahead' Grounding...")
        
        # Test a safe file read simulation
        action = {
            "type": "read_file",
            "path": "main.py"
        }
        
        simulation_result = await quantum_executor.simulate(action, context={"reason": "Self-test"})
        
        if simulation_result.get("status") == "success":
            print(f"[OK] Quantum Simulation Successful: {simulation_result.get('summary')}")
        else:
            print(f"[FAIL] Quantum Simulation Failed: {simulation_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Quantum Execution Check Error: {e}")
        return False
        
    # 4. Watchdog & Lifespan Import Check
    try:
        print("[-] Verifying Lifespan Watchdog Integrity...")
        import startup.lifespan as lifespan
        # We don't run the loops, just check if they import correctly
        print("[OK] Lifespan module imported correctly with New Nexus.")
    except Exception as e:
        print(f"[FAIL] Lifespan Import Error (Likely circular or missing import): {e}")
        return False

    print(f"\n[SUCCESS] Phase 17 Cognitive Core is STABLE and SYNCHRONIZED.")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_nexus_quantum_sync())
    if not success:
        sys.exit(1)
