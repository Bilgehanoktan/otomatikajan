
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import select, delete, func, and_
from db.models import Memory
from core.agi.learning.wisdom_synthesizer import wisdom_synthesizer
from core.agi.task_governance import ProjectTask, SubTask, TaskStatus

_log = logging.getLogger("agi_memory_pruner")

class MemoryPruner:
    """
    [Katman 59] Bilişsel Sıkıştırma (Cognitive Compaction) & Rüya Döngüsü.
    Düşük öncelikli gürültüyü temizler ve benzer anıları konsolide eder.
    """

    def __init__(self):
        self.min_importance = 0.2
        self.noise_age_hours = 48
        self.consolidation_threshold = 3 # Aynı kategoride 3+ benzer anı varsa birleştir

    async def dream_cycle(self, db):
        """Ana temizlik ve konsolidasyon döngüsü."""
        _log.info("[DREAM] Rüya döngüsü başlatıldı: Bilişsel temizlik yapılıyor.")
        
        # 1. Gürültü Temizliği (Pruning)
        await self.prune_noise(db)
        
        # 2. Benzer Anıları Konsolide Et (Consolidation)
        await self.consolidate_redundant(db)
        
        _log.info("[DREAM] Rüya döngüsü tamamlandı.")

    async def prune_noise(self, db):
        """Düşük öncelikli ve eski anıları temizler."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.noise_age_hours)
        
        stmt = delete(Memory).where(
            and_(
                Memory.importance < self.min_importance,
                Memory.created_at < cutoff,
                Memory.category != "semantic_wisdom" # Bilgeliği ASLA silme
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        _log.info(f"[DREAM-PRUNE] {result.rowcount} adet gürültü kaydı temizlendi.")

    async def consolidate_redundant(self, db):
        """Tekrarlayan veya çok benzer anıları tek bir 'Master Wisdom'da birleştirir."""
        # Kategori bazlı gruplama yaparak başla
        stmt = select(Memory.category, func.count(Memory.id)).group_by(Memory.category).having(func.count(Memory.id) >= self.consolidation_threshold)
        categories = (await db.execute(stmt)).all()
        
        for category, count in categories:
            if category == "semantic_wisdom":
                continue # Bilgelik zaten konsolide edilmiş veridir.

            # Bu kategorideki anıları çek
            mem_stmt = select(Memory).where(Memory.category == category).order_by(Memory.created_at.desc()).limit(10)
            memories = (await db.execute(mem_stmt)).scalars().all()
            
            if len(memories) < self.consolidation_threshold:
                continue

            # WisdomSynthesizer'ı birleştirme için kullan (Mock ProjectTask yapısı ile)
            _log.info(f"[DREAM-CONSOLIDATE] '{category}' kategorisinde {len(memories)} anı birleştiriliyor.")
            
            mock_task = ProjectTask(
                id=f"dream-merge-{category}",
                title=f"Consolidated Memory: {category}",
                description=f"Merging {len(memories)} granular experiences into a unified pattern."
            )
            
            # Alt görevlermiş gibi trace'leri doldur
            mock_task.subtasks = [
                SubTask(id=str(m.id), agent_id=m.agent_id, prompt="N/A", result=m.body, status=TaskStatus.COMPLETED)
                for m in memories
            ]
            
            wisdom = await wisdom_synthesizer.synthesize_from_task(mock_task)
            
            if wisdom:
                # Orijinal dağınık anıları sil ve yeni consolidated anıyı (synthesizer zaten yaptı) teyit et
                # (Synthesizer zaten save() yapıyor, biz sadece eskileri silmeliyiz)
                ids_to_delete = [m.id for m in memories]
                del_stmt = delete(Memory).where(Memory.id.in_(ids_to_delete))
                await db.execute(del_stmt)
                await db.commit()
                _log.info(f"[DREAM-CONSOLIDATE] {len(ids_to_delete)} anı tek bir bilgi paketine dönüştürüldü.")

memory_pruner = MemoryPruner()
