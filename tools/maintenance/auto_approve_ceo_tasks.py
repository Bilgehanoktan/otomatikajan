import asyncio
import os
import sys
import uuid

# PYTHONPATH set edilmeli
sys.path.append(os.getcwd())

from sqlalchemy import select
from packages.persistence.session import session_scope
from packages.persistence.models import CEOSuggestedTask, ImprovementOpportunity
from packages.orchestration.ceo.engine import get_ceo_engine

async def main():
    print("CEO Otomatik Onay Başlatılıyor...")
    
    async with session_scope() as db:
        # 1. Önerilen görevleri bul
        res = await db.execute(
            select(CEOSuggestedTask).where(CEOSuggestedTask.status == "suggested")
        )
        suggestions = res.scalars().all()
        
        if not suggestions:
            print("Onaylanacak öneri bulunamadı.")
            return

        print(f"{len(suggestions)} öneri bulundu. Onaylanıyor...")
        
        ceo = get_ceo_engine()
        for sug in suggestions:
            print(f"Onaylanıyor: {sug.title} (ID: {sug.id})")
            try:
                result = await ceo.manual_approve_suggestion(sug.id)
                if result.get("success"):
                    print(f"BAŞARILI: {sug.title} -> Proje ID: {result.get('project_id')}")
                else:
                    print(f"HATA: {sug.title} -> {result.get('error')}")
            except Exception as e:
                print(f"KRİTİK HATA: {sug.title} -> {e}")

        await db.commit()
    print("CEO Otomatik Onay tamamlandı.")

if __name__ == "__main__":
    asyncio.run(main())
