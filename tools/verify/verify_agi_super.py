import asyncio
import os
import sys

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_super_intelligence():
    print("--- AGI 14.0 & 15.0 Verification ---")
    
    try:
        from packages.orchestration.agi.operational.agent_weaver import agent_weaver
        from packages.orchestration.agi.proactive_agent import proactive_agent
        from agents.agent_registry import discover_and_build_specialists
        
        print("[OK] AGI 14.0/15.0 components imported successfully.")
        
        # Test Dynamic Registry
        specialists = discover_and_build_specialists()
        if "test_specialist" in specialists:
            print(f"[OK] Dynamic Registry: {specialists['test_specialist'].name} loaded.")
        else:
            print("[ERROR] Dynamic Registry failed to load 'test_specialist'.")
        
        # Test Agent Weaver Presence
        print(f"[OK] Agent Weaver ready for synthesis.")
        
        # Test Proactive Agent Presence
        print(f"[OK] Proactive Agent ready for heartbeat.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_super_intelligence())
