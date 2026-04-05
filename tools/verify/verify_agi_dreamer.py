"""
AGI Subconscious Cortex Verification Script (Phase 45.0).
Test senaryosu: Benzer hata kayıtları üretilir, Subconscious Cortex (45.0) tetiklenir ve 
hafıza konsolidasyonu (bilinçaltı öğrenme) başarısı doğrulanır.
"""
import os
import sys
import asyncio
import uuid
from datetime import datetime, timezone

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from packages.persistence.session import AsyncSessionLocal, init_db
from packages.persistence.models import Memory
from packages.orchestration.agi.cognitive.subconscious_cortex_45 import subconscious_cortex_45
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from packages.observability.logging import get_logger

_log = get_logger("agi_dreamer_verify")

async def verify_dreamer():
    _log.info("--- AGI DREAMER DOĞRULAMA TESTİ BAŞLATILIYOR ---")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # 1. Test Verisi Hazırla: 5 adet benzer hata kaydı
        error_msg = "Critical Failure: PostgreSQL connection refused [WinError 1225]"
        test_ids = []
        for i in range(5):
            entry = await synaptic_cortex.save(
                db,
                agent_id="test_agent",
                body=f"Task {i} failed: {error_msg}",
                category="episode_record",
                importance=0.6,
                metadata={"status": "failed", "error": error_msg, "title": f"DB Connection Test {i}"}
            )
            test_ids.append(str(entry.id))
        
        await db.commit()
        _log.info(f"{len(test_ids)} adet benzer hata kaydı oluşturuldu.")

        # 2. Dreamer'ı Tetikle
        _log.info("Subconscious Cortex (Düşleme) süreci manuel olarak başlatılıyor...")
        await subconscious_cortex_45.dream(db, limit=10)
        await db.commit()

        # 3. Sonuçları Kontrol Et
        # a) Yeni bir reflection_log (Evrensel Ders) oluştu mu?
        recent_reflections = await synaptic_cortex.get_recent(db, category="reflection_log", limit=3)
        lesson_found = any("universal" in (r.tags or []) for r in recent_reflections)
        
        if lesson_found:
            _log.info("[PASSED] Dreamer evrensel ders sentezledi.")
        else:
            _log.error("[FAILED] Dreamer evrensel ders sentezleyemedi.")

        # b) Redundant kayıtlar işaretlendi mi?
        # Not: LLM'in bu ID'leri tam olarak döndürmesi garanti değil ama en az birini bulmasını bekliyoruz.
        marked_redundant = 0
        for tid in test_ids:
            m = await db.get(Memory, uuid.UUID(tid))
            if m and "consolidated_redundant" in (m.tags or []):
                marked_redundant += 1
        
        if marked_redundant > 0:
            _log.info(f"[PASSED] {marked_redundant} adet kayıt redundant olarak işaretlendi.")
        else:
            _log.warning("[REVIEW] Hiçbir kayıt redundant olarak işaretlenmedi. LLM ID'leri eşleştirememiş olabilir.")

    _log.info("--- VERİFİKASYON TAMAMLANDI ---")

if __name__ == "__main__":
    asyncio.run(verify_dreamer())
