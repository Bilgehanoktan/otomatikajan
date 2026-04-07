import asyncio
import sys
import os
# Proje köke python path ekle
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from sqlalchemy import select, func
from packages.persistence.session import AsyncSessionLocal, init_db
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from packages.orchestration.agi.cognitive.motivation_engine import motivation_engine
from packages.persistence.models import Memory, Project
from packages.observability.logging import get_logger

_log = get_logger("agi_subconscious_audit")

async def audit_subconscious():
    """
    Sistemin 'bilinçaltı' metriklerini (hafıza, politika, nedensellik) denetler.
    """
    _log.info("--- AGI BİLİNÇALTI DENETİMİ BAŞLATILIYOR ---")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # 1. Hafıza İstatistikleri
        memory_count = await packages.persistence.scalar(select(func.count()).select_from(Memory))
        _log.info(f"Toplam Hafıza Kaydı (Episodes/Memories): {memory_count}")
        
        # 2. Episode Dağılımı (Kategori Bazlı)
        categories = await packages.persistence.execute(
            select(Memory.category, func.count()).group_by(Memory.category)
        )
        _log.info("Kategori Dağılımı:")
        for cat, cnt in categories:
            _log.info(f"  - {cat}: {cnt}")
        
        # 3. Politika (Policy) Durumu
        policies = await packages.persistence.scalar(
            select(func.count()).select_from(Memory).where(Memory.category == "policy")
        )
        _log.info(f"Aktif/Önerilen Politikalar: {policies}")
        
        # 4. Nedensellik (Causal) Bağlantıları
        all_memories = await packages.persistence.execute(select(Memory))
        causal_count = 0
        for m in all_memories.scalars():
            if m.metadata_ and "failure_diagnostics" in m.metadata_:
                causal_count += 1
        _log.info(f"Nedensel Analiz İçeren Kayıt Sayısı: {causal_count}")
        
        # 5. Proje Bütünlüğü
        projects = await packages.persistence.scalar(select(func.count()).select_from(Project))
        _log.info(f"Toplam Takip Edilen Proje: {projects}")
        
        # 6. Affective Core (Motivation) Durumu
        state = motivation_engine.current_state
        _log.info(f"--- AFFECTIVE CORE DURUMU ---")
        _log.info(f"  - Motivasyon: {state.motivation_level:.2f}")
        _log.info(f"  - Dayanıklılık: {state.resilience_score:.2f}")
        _log.info(f"  - Israr Politikası: {state.persistence_policy}")
        _log.info(f"  - Enerji Rezervi: {state.energy_reserve:.2f}")

    _log.info("--- DENETİM TAMAMLANDI ---")

if __name__ == "__main__":
    try:
        asyncio.run(audit_subconscious())
    except Exception as e:
        _log.error(f"Denetim sırasında kritik hata: {e}")
        sys.exit(1)
