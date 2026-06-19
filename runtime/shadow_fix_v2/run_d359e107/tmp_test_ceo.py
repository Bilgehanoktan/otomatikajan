import asyncio
import uuid
import logging
import os
import sys

# Add current directory to path for imports
sys.path.append(os.getcwd())

from services.orchestration.ceo.engine import get_ceo_engine
from libs.db.session import session_scope
from libs.db.models import ImprovementOpportunity, CEOSuggestedTask, Project

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_ceo")

async def test_ceo_flow():
    ceo = get_ceo_engine()
    
    print("\n--- TEST 1: Scan & Findings Detay Kontrolü ---")
    async with session_scope() as db:
        from sqlalchemy import select
        
        # 1. Mock bir fırsat ve öneri oluşturalım
        op_id = uuid.uuid4()
        op = ImprovementOpportunity(
            id=op_id,
            source_type="security",
            title="Test Zafiyeti - " + str(op_id)[:8],
            description="Bu bir test analizidir.",
            category="security",
            severity="high",
            priority_score=85,
            status="open",
            evidence_detail="mock_failure",
            affected_files=["test.py"]
        )
        db.add(op)
        
        sug_id = uuid.uuid4()
        sug = CEOSuggestedTask(
            id=sug_id,
            opportunity_id=op_id,
            title="Sistemi Yama - " + str(sug_id)[:8],
            description="Otomatik yama yükle.",
            priority=8,
            status="suggested",
            plan_hierarchy={"step_index": 0, "strategic_objective": "Stabilite Artışı"}
        )
        db.add(sug)
        await db.commit()
        print(f"[*] Test verileri oluşturuldu. Sug ID: {sug_id}")

    print("\n--- TEST 2: Manuel Onaylama (Manual Approval) ---")
    # Oluşturduğumuz öneriyi onaylayalım
    res_approve = await ceo.manual_approve_suggestion(sug_id)
    print(f"[*] Onay Sonucu: {res_approve}")
    
    if res_approve.get("success"):
        proj_id_str = res_approve["project_id"]
        proj_id = uuid.UUID(proj_id_str)
        async with session_scope() as db:
            from sqlalchemy import select
            res_proj = await db.execute(select(Project).where(Project.id == proj_id))
            new_proj = res_proj.scalars().first()
            if new_proj:
                print(f"[SUCCESS] Yeni Proje Oluştu: {new_proj.title}")
                print(f"[*] Project Notes: {new_proj.notes}")
                print(f"[*] Project Status: {new_proj.status}")
                print(f"[*] Job ID: {getattr(new_proj, 'job_id', 'N/A')}")
            else:
                print("[FAIL] Proje veritabanında bulunamadı!")
    else:
        print(f"[FAIL] Onaylama hatası: {res_approve.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_ceo_flow())
