import asyncio
import sys
import os
from sqlalchemy import select, func
from db.session import AsyncSessionLocal
from db.models import Memory, Project
from observability.logging import get_logger

_log = get_logger("agi_subconscious_audit")

async def audit_subconscious():
    """
    Sistemin 'bilinçaltı' metriklerini (hafıza, politika, nedensellik) denetler.
    """
    _log.info("--- AGI BİLİNÇALTI DENETİMİ BAŞLATILIYOR ---")
    
    async with AsyncSessionLocal() as db:
        # 1. Hafıza İstatistikleri
        memory_count = await db.scalar(select(func.count()).select_from(Memory))
        _log.info(f"Toplam Hafıza Kaydı (Episodes/Memories): {memory_count}")
        
        # 2. Episode Dağılımı (Kategori Bazlı)
        categories = await db.execute(
            select(Memory.category, func.count()).group_by(Memory.category)
        )
        _log.info("Kategori Dağılımı:")
        for cat, cnt in categories:
            _log.info(f"  - {cat}: {cnt}")
        
        # 3. Politika (Policy) Durumu
        policies = await db.scalar(
            select(func.count()).select_from(Memory).where(Memory.category == "policy")
        )
        _log.info(f"Aktif/Önerilen Politikalar: {policies}")
        
        # 4. Nedensellik (Causal) Bağlantıları
        all_memories = await db.execute(select(Memory))
        causal_count = 0
        for m in all_memories.scalars():
            if m.metadata_ and "failure_diagnostics" in m.metadata_:
                causal_count += 1
        _log.info(f"Nedensel Analiz İçeren Kayıt Sayısı: {causal_count}")
        
        # 5. Proje Bütünlüğü
        projects = await db.scalar(select(func.count()).select_from(Project))
        _log.info(f"Toplam Takip Edilen Proje: {projects}")

    _log.info("--- DENETİM TAMAMLANDI ---")

if __name__ == "__main__":
    try:
        asyncio.run(audit_subconscious())
    except Exception as e:
        _log.error(f"Denetim sırasında kritik hata: {e}")
        sys.exit(1)
