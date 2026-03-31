import asyncio
import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from db.session import session_scope
from db.models import SkillExecutionLog, ImprovementOpportunity, Project
from core.agi.cognitive.synaptic_cortex import synaptic_cortex

_log = get_logger("agi_reflection")

class ReflectionCortex:
    """
    Cognitive Core (Katman 21): Reflection Cortex.
    AGI'nin 'Öz-Eleştiri' ve 'Bilişsel Analiz' katmanı.
    Ajan performansını izler, sistemik tıkanıklıkları (Cognitive Bottlenecks) bulur.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def run_reflection_cycle(self, db: Optional[AsyncSession] = None):
        """Bilişsel tarama döngüsünü (Reflection Cycle) çalıştırır."""
        _log.info("[REFLECTION] Bilişsel yansıma döngüsü başlatıldı.")
        
        if db:
            await self._perform_analysis(db)
        else:
            async with session_scope() as new_db:
                await self._perform_analysis(new_db)

    async def _perform_analysis(self, db: AsyncSession):
        # 1. Başarısızlık Oranlarını Hesapla
        stats = await self._get_agent_stats(db)
        
        # 2. Kritik Tıkanıklıkları Bul (Failure Rate > 30%)
        bottlenecks = [s for s in stats if s["failure_rate"] > 0.3]
        
        if not bottlenecks:
            _log.info("[REFLECTION] Ajan performansı sağlıklı bulundu. Kritik tıkanıklık yok.")
            return

        # 3. Neden Analizi (Root Cause Analysis via LLM)
        for bn in bottlenecks:
            await self._diagnose_and_propose_repair(db, bn)

    async def _get_agent_stats(self, db: AsyncSession) -> List[Dict]:
        """Ajan ve beceri bazlı başarı istatistiklerini getirir."""
        q = select(
            SkillExecutionLog.agent_id,
            SkillExecutionLog.skill_id,
            func.count(SkillExecutionLog.id).label("total"),
            func.sum(case((SkillExecutionLog.success == False, 1), else_=0)).label("fails")
        ).group_by(SkillExecutionLog.agent_id, SkillExecutionLog.skill_id).limit(20)
        
        result = await db.execute(q)
        rows = result.all()
        
        stats = []
        for row in rows:
            fails = row.fails or 0
            total = row.total or 1
            stats.append({
                "agent_id": row.agent_id,
                "skill_id": row.skill_id,
                "total": total,
                "fails": fails,
                "failure_rate": fails / total
            })
        return stats

    async def _diagnose_and_propose_repair(self, db: AsyncSession, bottleneck: Dict):
        """Tespit edilen bir tıkanıklık için çözüm önerisi geliştirir."""
        _log.warning(f"[REFLECTION] Kritik tıkanıklık tespit edildi: {bottleneck['agent_id']} ({bottleneck['skill_id']})")
        
        # Son hata detaylarını al
        logs_q = select(SkillExecutionLog.summary).where(
            SkillExecutionLog.agent_id == bottleneck["agent_id"],
            SkillExecutionLog.success == False
        ).limit(3)
        logs_res = await db.execute(logs_q)
        errors = list(logs_res.scalars().all())
        
        prompt = f"""
        Sistemde bir 'Bilişsel Tıkanıklık' (Cognitive Bottleneck) tespit edildi. 
        Ajan: {bottleneck['agent_id']}
        Beceri: {bottleneck['skill_id']}
        Hata Oranı: %{bottleneck['failure_rate'] * 100:.1f}
        
        SON HATALAR:
        {chr(10).join(errors)}
        
        Bu ajanın neden başarısız olduğunu analiz et ve bir 'Bilişsel Onarım' (Cognitive Repair) planı öner.
        Öneri şu JSON formatında olmalı:
        {{
            "root_cause": "Neden başarısız oluyor?",
            "repair_action": "System prompt güncellemesi | Model değişimi | Yeni beceri enjeksiyonu",
            "repair_detail": "Onarımın teknik detayı",
            "urgency": "high|medium|low"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="diagnostic_psychologist",
                prompt=prompt,
                system_prompt="Sen AGI'nin öz-analiz, yansıma ve bilişsel onarım uzmanısın."
            )
            
            import json
            import re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                repair_data = json.loads(match.group())
                await self._create_improvement_opportunity(db, repair_data, bottleneck)
                
        except Exception as e:
            _log.error(f"[REFLECTION] Onarım planı sentezleme hatası: {e}")

    async def _create_improvement_opportunity(self, db: AsyncSession, data: Dict, bn: Dict):
        """Teşhis sonuçlarını sistemin iyileştirme deposuna kaydeder. (Idempotent Upsert)"""
        p_hash = ImprovementOpportunity.generate_hash("cog_diag", f"{bn['agent_id']}:{bn['skill_id']}")
        
        stmt = select(ImprovementOpportunity).where(ImprovementOpportunity.pattern_hash == p_hash)
        res = await db.execute(stmt)
        existing_opp = res.scalar_one_or_none()
        
        if existing_opp:
            _log.info(f"[REFLECTION] Mevcut gelişim fırsatı güncelleniyor: {existing_opp.id}")
            existing_opp.description = f"RECURRING Root Cause: {data['root_cause']}\nRepair: {data['repair_action']}"
            existing_opp.evidence_detail = f"Updated Evidence: {data['repair_detail']}"
            existing_opp.severity = data['urgency']
            existing_opp.updated_at = datetime.now(timezone.utc)
            opp_id = existing_opp.id
        else:
            opp = ImprovementOpportunity(
                source_type="cognitive_diagnostic",
                source_ref=f"{bn['agent_id']}:{bn['skill_id']}",
                title=f"Cognitive Repair: {bn['agent_id']}",
                description=f"Root Cause: {data['root_cause']}\nRepair: {data['repair_action']}",
                severity=data['urgency'],
                category="reliability",
                evidence_detail=data['repair_detail'],
                pattern_hash=p_hash
            )
            db.add(opp)
            await db.flush()
            opp_id = opp.id
            _log.info(f"[REFLECTION] Yeni bilişsel onarım fırsatı kaydedildi: {opp_id}")
        
        await db.flush()
        
        # Faz 22: Teşhisi SynapticCortex'e kaydet (Kalıcı Deneyim)
        await synaptic_cortex.save(
            db=db,
            agent_id="reflection_cortex",
            body=f"Reflection Log: {bn['agent_id']} failure rate %{bn['failure_rate']*100:.1f}. Root Cause: {data['root_cause']}",
            category="reflection_log",
            importance=0.8,
            metadata={
                "agent_id": bn['agent_id'],
                "skill_id": bn['skill_id'],
                "repair_action": data['repair_action'],
                "opportunity_id": str(opp_id)
            }
        )
        
        _log.info(f"[REFLECTION] Bilişsel onarım kaydı tamamlandı: {opp_id}")

# Singleton Instance
reflection_cortex = ReflectionCortex()

# Compatibility Alias
DiagnosticNode = ReflectionCortex

# --- Background Task Definition ---
async def start_reflection_loop():
    from core.agi.monitoring.token_budgeter import token_budgeter
    while True:
        try:
            health = await token_budgeter.check_health()
            score = health["health_score"]
            
            if score > 0.8:
                delay = 3600 * 6 # 6 saat
            elif score > 0.4:
                delay = 86400    # 24 saat
            else:
                delay = 86400 * 2 # 48 saat
                _log.warning(f"[REFLECTION] Metabolizma kısıtlı, yansıma döngüsü yavaşlatıldı: {delay}s")

            await reflection_cortex.run_reflection_cycle()
            await asyncio.sleep(delay)
            
        except Exception as e:
            _log.error(f"[REFLECTION] Background loop error: {e}")
            await asyncio.sleep(600)
