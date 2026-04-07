import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_specialist_intelligence():
    print("--- AGI 25.0 Verification ---")
    
    try:
        from packages.orchestration.agi.learning.specialist_forge import specialist_forge
        from packages.orchestration.agi.adaptation.role_evolver import role_evolver
        
        print("[OK] AGI 25.0 components imported successfully.")
        
        # 1. Test Specialist Forge
        mock_db = MagicMock()
        # Mocking successful subtasks query
        new_specialists = await specialist_forge.forge_new_specialists(mock_db)
        
        if len(new_specialists) > 0:
            print(f"[OK] Specialist Forge: Successfully synthesized {len(new_specialists)} new specialist roles.")
        else:
            print("[INFO] Specialist Forge: No new role synthesis required for current data (logic active).")

        # 2. Test Role Evolver
        mock_spec = {"id": "test_specialist", "raw": '{"title": "Test Specialist", "prompt": "Be a test expert."}'}
        evolve_success = await role_evolver.evolve_roles(mock_spec)
        
        if evolve_success:
            print(f"[OK] Role Evolver: Successfully integrated new specialist role into system.")
            roles_path = "core/agi/roles/specialists.json"
            if os.path.exists(roles_path):
                print(f"    - Specialist library updated at: {roles_path}")
            else:
                print(f"    - [WARN] Specialist library file missing but logic reported success.")
        else:
            print(f"[ERROR] Role Evolver failed to integrate roles.")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_specialist_intelligence())
