import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_consciousness():
    print("--- AGI 30.0 Verification ---")
    
    try:
        from packages.orchestration.agi.consciousness.global_workspace import global_workspace
        from packages.orchestration.agi.consciousness.neural_core_orchestrator import neural_core_orchestrator
        
        print("[OK] AGI 30.0 components imported successfully.")
        
        # 1. Test Global Workspace
        print("[INFO] Global Workspace: Broadcasting sample thought...")
        global_workspace.broadcast("VerificationModule", "Consciousness active.", importance=1.0)
        qualia = global_workspace.get_current_qualia()
        
        if len(qualia.get("recent_thoughts", [])) > 0:
            print(f"[OK] Global Workspace: Thought broadcast synchronized. Recent: {qualia['recent_thoughts'][-1]['content']}")
        else:
            print("[ERROR] Global Workspace failed to record thought.")

        # 2. Test Neural Core Orchestrator
        mock_db = MagicMock()
        print("[INFO] Neural Core Orchestrator: Running full Mind Cycle...")
        await neural_core_orchestrator.run_mind_cycle(mock_db)
        
        print("[OK] Integrated Orchestrator: Unified Mind Cycle executed successfully.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_consciousness())
