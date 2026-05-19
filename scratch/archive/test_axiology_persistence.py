import asyncio
import json
import uuid
from services.orchestration.agi.cognitive.axiology_engine import AxiologyEngine
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SovereignEvidence
from sqlalchemy import select

async def test_axiology_persistence():
    print("--- Axiology Persistence & API Test ---")
    engine = AxiologyEngine()
    
    # 1. Denetim Tetikle
    print("1. Denetim tetikleniyor...")
    target_plan = "Kritik veritabanÄ±nÄ± optimize et ve gereksiz loglarÄ± temizle."
    result = await engine.evaluate_alignment(target_plan, context="db_cleanup_plan")
    print(f"Denetim KararÄ±: {result['decision']}")
    
    # 2. VeritabanÄ±nda KaydÄ± Kontrol Et
    print("2. VeritabanÄ± kaydÄ± kontrol ediliyor...")
    print(f"Audit Decision: {result['decision']}")
    
    # 2. Veritabaninda Kaydi Kontrol Et
    print("2. Checking database record...")
    async with AsyncSessionLocal() as db:
        q = select(SovereignEvidence).where(SovereignEvidence.evidence_type == "axiology_audit").order_by(SovereignEvidence.created_at.desc()).limit(1)
        res = await db.execute(q)
        evidence = res.scalar_one_or_none()
        
        if evidence:
            print(f"SUCCESS: Database record found! ID: {evidence.id}")
            # Use json.dumps with ensure_ascii=False to be safe or just standard
            print(f"Record Payload (truncated): {str(evidence.payload)[:200]}")
        else:
            print("ERROR: Database record NOT found!")
            return

    print("\n--- TEST COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(test_axiology_persistence())
