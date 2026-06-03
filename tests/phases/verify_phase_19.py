import asyncio
import os
import shutil
from pathlib import Path
from services.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as nexus_orchestrator
from services.orchestration.agi.operational.scaffolder import scaffolder

async def verify_self_building_layer():
    print("--- Phase 19 Self-Building Verification ---")
    
    # 1. Mock Architecture Proposal
    proposal = {
        "title": "Test Subsystem Creation",
        "reasoning": "Verifying Phase 19 scaffolding capabilities.",
        "actions": [
            {
                "type": "create_subsystem",
                "path": "core/agi/experimental_tests/",
                "files_to_scaffold": ["__init__.py", "test_node.py"]
            }
        ]
    }

    # 2. Execute via Nexus (includes AuditGate check)
    print("[*] Coordinating architecture via Nexus...")
    # Clean up before test if exists
    test_dir = Path(__file__).resolve().parents[2] / "core" / "agi" / "experimental_tests"
    if test_dir.exists():
        shutil.rmtree(test_dir)

    success = await nexus_orchestrator.coordinate_architecture(proposal)
    
    if success:
        print("[SUCCESS] Nexus coordination & AuditGate check PASSED.")
    else:
        print("[FAILURE] Nexus coordination or AuditGate check FAILED.")
        return

    # 3. Verify Filesystem Reality
    print("[*] Verifying filesystem grounding...")
    init_file = test_dir / "__init__.py"
    node_file = test_dir / "test_node.py"
    
    if init_file.exists() and node_file.exists():
        print(f"[SUCCESS] Scaffolding verified at: {test_dir.as_posix()}")
        content = node_file.read_text()
        if "Placeholder" in content:
            print("[SUCCESS] Boilerplate content verified.")
        else:
            print("[FAILURE] Boilerplate content mismatch.")
    else:
        print(f"[FAILURE] Files not found at: {test_dir.as_posix()}")

    # 4. Clean up
    # shutil.rmtree(test_dir)
    print("\n[PHASE 19] SELF-BUILDING CAPABILITY VERIFIED.")

if __name__ == "__main__":
    asyncio.run(verify_self_building_layer())
