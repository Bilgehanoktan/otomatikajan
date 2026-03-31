import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, desc, update, case
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger
from db.session import session_scope
from db.models import SkillExecutionLog, ImprovementOpportunity, Memory
from core.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store

_log = get_logger("agi_synapse_stabilizer")

class SynapseStabilizer:
    """
    AGI'nin 'Bilişsel Kemikleşme' ve 'Hafıza Stabilizasyonu' katmanı.
    Geçici onarımların (Phase 21) ve önerilen politikaların (USER update) 
    başarısını izler ve onları 'İçsel Bilgi' (Innate Knowledge) haline getirir.
    """

    async def run_stabilization_cycle(self):
        """Stabilizasyon döngüsünü çalıştırır."""
        _log.info("[STABILIZER] Bilişsel stabilizasyon döngüsü başlatıldı.")
        
        async with session_scope() as db:
            # 1. Tamamlanmış Onarımları Bul (Resolved Improvement Opportunities)
            resolved_opps = await self._get_resolved_opportunities(db)
            
            for opp in resolved_opps:
                success_rate = await self._verify_repair_effect(db, opp)
                
                if success_rate >= 0.9: # %90+ başarı
                    await self._harden_synapse_memory(db, opp)
                elif success_rate < 0.5: # Başarısız onarım
                    await self._revert_or_re_diagnose(db, opp)

    async def _get_resolved_opportunities(self, db: AsyncSession) -> List[ImprovementOpportunity]:
        q = select(ImprovementOpportunity).where(ImprovementOpportunity.status == "resolved")
        result = await db.execute(q)
        return list(result.scalars().all())

    async def _verify_repair_effect(self, db: AsyncSession, opp: ImprovementOpportunity) -> float:
        """Onarımın (Repair) ardından ajanın başarı oranını kontrol eder."""
        # source_ref formatı genellikle "agent_id:skill_id"
        if not opp.source_ref or ":" not in opp.source_ref:
            return 0.0
            
        agent_id, skill_id = opp.source_ref.split(":")
        
        # Onarım sonrası (created_at + 1h) logları getir
        q = select(
            func.count(SkillExecutionLog.id).label("total"),
            func.sum(case((SkillExecutionLog.success == True, 1), else_=0)).label("successes")
        ).where(
            SkillExecutionLog.agent_id == agent_id,
            SkillExecutionLog.skill_id == skill_id,
            SkillExecutionLog.created_at > opp.created_at
        )
        
        result = await db.execute(q)
        res = result.fetchone()
        
        if not res or not res.total:
            return 0.0
            
        return res.successes / res.total

    async def _harden_synapse_memory(self, db: AsyncSession, opp: ImprovementOpportunity):
        """Başarılı bir onarımı 'Innate Knowledge' (Importance: 1.0) olarak işaretler."""
        _log.info(f"[STABILIZER] Onarım başarılı bulundu. Synapse sertleştiriliyor: {opp.title}")
        
        # İlgili Synapse kaydını bul (opportunity_id metadata içinde saklanır)
        # SQLAlchemy JSONB query syntax:
        q = select(Memory).where(Memory.metadata_["opportunity_id"].astext == str(opp.id))
        result = await db.execute(q)
        mem = result.scalar_one_or_none()
        
        if mem:
            mem.importance = 1.0
            mem.tags = list(set((mem.tags or []) + ["innate", "hardened"]))
            _log.info(f"[STABILIZER] Synapse 'Innate' (İçsel) olarak güncellendi: {mem.id}")
            
            # Opportunity'yi 'archived' yap
            opp.status = "archived"
            await db.flush()

    async def _revert_or_re_diagnose(self, db: AsyncSession, opp: ImprovementOpportunity):
        """Başarısız bir onarımı geri alır veya yeniden teşhis için bayraklar."""
        _log.warning(f"[STABILIZER] Onarım ETKİSİZ! Yeniden teşhis gerekecek: {opp.title}")
        opp.status = "failed_repair"
        await db.flush()

async def start_synapse_stabilization_loop():
    from core.agi.monitoring.token_budgeter import token_budgeter
    stabilizer = SynapseStabilizer()
    
    while True:
        try:
            # ── ADAPTIVE SLEEP (Phase 24) ──
            health = await token_budgeter.check_health()
            score = health["health_score"]
            
            if score > 0.8:
                delay = 3600 * 12 # 12 saat (Normal)
            elif score > 0.4:
                delay = 86400 * 3  # 3 gün (Stressed)
            else:
                delay = 86400 * 7 # 1 hafta (Critical)
                _log.warning(f"[STABILIZER] Metabolizma kısıtlı, bellek sertleştirme yavaşlatıldı: {delay}s")

            await stabilizer.run_stabilization_cycle()
            await asyncio.sleep(delay)
            
        except Exception as e:
            _log.error(f"[STABILIZER] Background loop error: {e}")
            await asyncio.sleep(600)
