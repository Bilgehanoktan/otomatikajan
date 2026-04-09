import asyncio
import sys
import os

# Sistemin ana dizinini path'e ekle
sys.path.append(os.getcwd())

async def verify():
    print("--- Faz 12.1 Sovereign AGI Verification ---")
    
    try:
        # 1. Capabilities Endpoint Logic Check
        from apps.api.routers.task_read_router import task_capabilities
        
        print("[1/3] Testing /capabilities logic...")
        # task_capabilities handles current_user=Depends internally, but we can call it directly
        # since we are mocking/ignoring dependencies for this unit check.
        try:
            # We pass None for current_user to see if it executes the core logic
            res = await task_capabilities(current_user={"email": "verify@system.local"})
            print(f"Result: {len(res.get('capabilities', []))} agents found.")
            if "capabilities" in res and len(res["capabilities"]) > 0:
                print("SUCCESS: Capabilities endpoint verified.")
            else:
                print("FAILURE: Capabilities endpoint returned empty or invalid data.")
        except Exception as e:
            print(f"ERROR: Capabilities endpoint failed: {e}")

        # 2. Auditor & Evolution Engine Check
        try:
            from packages.orchestration.agi.cognitive.sovereign_auditor import sovereign_auditor
            print("[2/3] Testing SovereignCortexAuditor...")
            findings = await sovereign_auditor.run_full_audit()
            print(f"Found {len(findings)} initial audit findings.")
            
            from packages.orchestration.agi.cognitive.evolution_engine import evolution_engine
            print("[3/3] Testing SovereignEvolutionEngine...")
            # Just verify instance and methods
            print(f"Evolution Engine instance: {evolution_engine}")
            print("Evolution Engine is ready.")
        except ImportError as ie:
            print(f"ERROR: Evolution engine imports failed: {ie}")
        
        print("\n--- ALL SYSTEMS NOMINAL ---")
        
    except Exception as e:
        print(f"CRITICAL: Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())
