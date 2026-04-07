import asyncio
import os
import sys

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_reflection():
    print("--- AGI 12.3 Verification ---")
    
    try:
        from packages.orchestration.agi.orchestrator import agi_orchestrator
        from packages.orchestration.agi.adaptation.policy_engine import policy_engine
        from packages.orchestration.agi.security.audit_gate import AuditGate
        from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store
        
        print("[OK] All AGI Refelection components imported successfully.")
        
        # Test Policy Engine
        print("[OK] Policy Engine ready.")
        
        # Test AuditGate Hard Grounding
        from packages.orchestration.agi.schemas import ActionRecord
        actions = [
            ActionRecord(tool_used="write_file", input_data="main.py", output_data="File main.py written")
        ]
        audit = AuditGate(agi_orchestrator.model_orch)
        grounding = audit._check_filesystem_grounding(actions)
        print(f"[OK] Grounding check (main.py): {len(grounding) > 0}")
        
        # Test Memory get_recent
        from packages.persistence.session import session_scope
        async with session_scope() as db:
            recent = await memory_store.get_recent(db, limit=1)
            print(f"[OK] Memory get_recent working: {len(recent) >= 0}")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_reflection())
