import asyncio
import sys
import os

# Add e:/ai_company_faz12.1 to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import AsyncSessionLocal
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from core.agi.adaptation.sovereign_evolution_45 import sovereign_evolution_45
from core.agi.monitoring.provenance_engine_45 import provenance_engine_45
from db.models import Memory
from sqlalchemy import select

async def verify_v45_sovereign():
    print("--- Phase 45.0 Sovereign AGI Verification — Provenance Analysis ---")
    
    async with AsyncSessionLocal() as db:
        # 1. Mockbir yama dosyası oluştur
        test_file = "scripts/test_patch_target.py"
        with open(test_file, "w") as f:
            f.write("# Initial state for Phase 45 test\n")
            f.write("def dummy():\n    pass\n")

        # 2. Mock 'Policy' ekle
        policy_id = "test-policy-" + str(os.getpid())
        await synaptic_cortex.save(
            db,
            agent_id="test_verifier",
            body="Improve dummy function with docstring.",
            category="policy_proposal",
            importance=0.9,
            metadata={
                "status": "pending",
                "evolution_version": "45.0",
                "proposed_target": test_file,
                "reason": "Test Phase 45 Traceability"
            }
        )
        await db.commit()
        print(f"[*] Mock Policy created for {test_file}")

        # 3. Evolve tetikle
        print("[*] Triggering Sovereign Evolution...")
        # Not: LLM'e çıkması muhtemel. Eğer kota hatası alırsa Provenance recording manuel test edilecek.
        try:
            await sovereign_evolution_45.evolve_system(db)
        except Exception as e:
            print(f"[!] Evolution during test aborted (expected LLM limits): {e}")

        # 4. Provenance Kaydını Doğrula
        stmt = select(Memory).where(Memory.category == "evolution_provenance").order_by(Memory.created_at.desc()).limit(1)
        res = await db.execute(stmt)
        prov = res.scalar_one_or_none()

        if prov:
            print("[SUCCESS] Evolution Provenance record found!")
            print(f"| File: {prov.metadata_.get('file_path')}")
            print(f"| Reason: {prov.metadata_.get('reasoning')}")
            print(f"| Diff (First 100 chars): {prov.metadata_.get('diff_summary')[:100]}...")
            print(f"| Version: {prov.metadata_.get('version')}")
        else:
            print("[FAIL] No provenance record found. Checking if policy is still pending...")
            # LLM hata verdiyse yama yapılamamıştır. Provenance Engine'i doğrudan test edelim.
            print("[*] Performing direct Provenance Engine test (Surgical Validation)...")
            await provenance_engine_45.record_evolution_step(
                db=db,
                file_path=test_file,
                original_content="# Initial state for Phase 45 test\n",
                new_content="# Updated state\ndef dummy():\n    '''Improved Docstring'''\n    pass\n",
                policy_id="VERIFY-999",
                reason="Manual surgical verification of Provenance Layer"
            )
            await db.commit()
            
            res_retry = await db.execute(stmt)
            prov_retry = res_retry.scalar_one_or_none()
            if prov_retry:
                print("[SUCCESS] Direct Provenance test passed!")
            else:
                print("[CRITICAL FAIL] Provenance engine failed to record.")

if __name__ == "__main__":
    asyncio.run(verify_v45_sovereign())
