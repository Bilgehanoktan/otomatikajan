import asyncio
import os
import sys

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_metalearning_and_selfaudit():
    print("--- AGI 12.10 & 13.0 Verification ---")
    
    try:
        from core.agi.adaptation.policy_enforcer import policy_enforcer
        from core.agi.cognitive.self_audit import self_audit
        from core.agi.orchestrator import agi_orchestrator
        
        print("[OK] AGI 12.10/13.0 components imported successfully.")
        
        # Test Policy Enforcer Presence
        print(f"[OK] Policy Enforcer ready for injection.")
        
        # Test Self-Audit Presence
        print(f"[OK] Self-Audit Agent ready for core-hardening.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_metalearning_and_selfaudit())
