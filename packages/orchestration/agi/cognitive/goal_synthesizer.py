import asyncio
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from packages.observability.logging import get_logger
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.persistence.session import session_scope, get_db
from packages.persistence.repository import ImprovementRepository, ProjectRepository, EventLogRepository
from packages.orchestration.agi.schemas import SourceType
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex

_log = get_logger("goal_synthesizer")

class GoalSynthesizer:
    """
    Sistemin operasyonel geçmişini ve iyileştirme fırsatlarını analiz ederek
    yüksek seviyeli stratejik 'Misyonlar' (Hedefler) sentezleyen motor.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def run_synthesis_cycle(self):
        """
        Düşük seviyeli iyileştirme fırsatlarını (ImprovementOpportunity) analiz eder
        ve bunları yüksek seviyeli 'Nexus' hedeflerine dönüştürür.
        """
        _log.info("[GOAL_SYNTH] Hedef sentez döngüsü başlatıldı.")
        
        # Faz 12.6: Bellekten (Memory) Otonom İyileştirme Fırsatları Çıkar
        await self._extract_evolution_opportunities_from_memory()
        
        # 1. Ham Veri (Opportunities) Toplama
        async with session_scope() as db:
            opportunities = await ImprovementRepository.list_open(limit=50)
        
        if len(opportunities) < 3:
            _log.info("[GOAL_SYNTH] Sentez için yeterli fırsat birikmedi (< 3).")
            return

        # 2. Örüntü Tanıma ve Kümeleme (Pattern Recognition)
        clusters = self._cluster_opportunities(opportunities)
        
        # 3. Misyon Sentezi (Mission Synthesis)
        for category, opps in clusters.items():
            if len(opps) >= 2: # Aynı kategoride 2 veya daha fazla fırsat varsa misyon oluştur
                await self._synthesize_strategic_mission(category, opps)

    def _cluster_opportunities(self, opportunities: List[Any]) -> Dict[str, List[Any]]:
        """Fırsatları kategorilerine göre gruplar."""
        clusters = {}
        for opp in opportunities:
            cat = opp.category or "general"
            clusters.setdefault(cat, []).append(opp)
        return clusters

    async def _synthesize_strategic_mission(self, category: str, opportunities: List[Any]):
        """
        Kümelenmiş fırsatlardan tek bir 'Büyük Strateji' (Hedef) oluşturur.
        """
        _log.warning(f"[GOAL_SYNTH] '{category}' kategorisi için Stratejik Misyon sentezleniyor (Fırsat sayısı: {len(opportunities)})")
        
        # 1. LLM ile Konsolidasyon ve Frame Oluşturma
        input_data = "\n".join([f"- {o.title}: {o.description}" for o in opportunities])
        
        prompt = f"""
        Aşağıdaki düşük seviyeli iyileştirme fırsatlarını analiz et ve bunları tek bir 
        'Stratejik Misyon' (Yüksek seviyeli hedef) altında birleştir.
        
        HEDEFLER:
        {input_data}
        
        Yanıtı aşağıdaki JSON formatında ver (Ajanlar bu misyonu Nexus üzerinden yürütecek):
        {{
            "title": "Misyon Başlığı",
            "mission_statement": "Bu misyonun temel amacı ve kapsamı",
            "priority": "high|medium|low",
            "expected_outcome": "Tamamlandığında sistemdeki hangi dar boğazlar çözülmüş olacak?",
            "suggested_agent": "architect|devops|security_expert..."
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir Sistem Mimarı ve Stratejistsin. Dağınık problemleri merkezi çözümlere dönüştürürsün."
            )
            
            # JSON Parse ve Misyon Kaydı
            from packages.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator
            mission_data = self._parse_json(response.content)
            
            if mission_data:
                # Nexus üzerinden yeni bir koordinasyon başlat
                _log.info(f"[GOAL_SYNTH] Yeni Misyon Sentezlendi: {mission_data['title']}")
                
                # Gerçekte bir Project oluşturup koordinasyona sokuyoruz
                async with session_scope() as db:
                    project = await ProjectRepository.create(
                        db,
                        title=f"MISSION: {mission_data['title']}",
                        description=mission_data['mission_statement'],
                        source=SourceType.SYSTEM_EVOLUTION.value,
                        priority=mission_data['priority'],
                        assigned_agent=mission_data['suggested_agent'],
                        notes=f"Sentezlenen fırsatlar: {len(opportunities)}",
                        status="pending"
                    )
                    
                    # Fırsatları 'Misyon Altına Alındı' olarak işaretle (resolved)
                    for opp in opportunities:
                        await ImprovementRepository.mark_resolved(db, opp.id)
                    
                    await db.commit()
                
                # Nexus'a yeni hedefi bildir (opsiyonel, watchdog yakalar)
                # await nexus_orchestrator.coordinate_goal(...)
                
        except Exception as e:
            _log.error(f"[GOAL_SYNTH] Misyon sentez hatası: {e}")

    async def _extract_evolution_opportunities_from_memory(self):
        """UGC'deki negatif örüntüleri analiz eder ve iyileştirme fırsatları üretir."""
        async with get_db() as db:
            failures = await synaptic_cortex.get_negative_patterns(db, limit=20)
        
        if not failures: return
        
        _log.info(f"[GOAL_SYNTH] {len(failures)} adet negatif örüntü analiz ediliyor...")
        
        input_text = "\n".join([f"- {f['body']} (Metadata: {f['metadata']})" for f in failures])
        
        prompt = f"""
        Sovereign AGI Sistem Günlükleri (Hatalar):
        {input_text}
        
        Yukarıdaki hataları analiz et. Tekrarlayan bir dar boğaz veya mimari zayıflık var mı?
        Eğer varsa, bu zayıflığı gidermek için bir 'İyileştirme Fırsatı' (Improvement Opportunity) üret.
        
        Yanıtı şu JSON listesi formatında ver:
        [
          {{
            "title": "İyileştirme Başlığı",
            "description": "Kök neden ve önerilen çözüm",
            "severity": "high|medium",
            "category": "architecture|reliability|logic"
          }}
        ]
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="critic",
                prompt=prompt,
                system_prompt="Sen bir Bilişsel Denetçi Ajansın (Cognitive Auditor)."
            )
            
            opportunities = self._parse_json(response.content)
            if not isinstance(opportunities, list): opportunities = [opportunities] if opportunities else []
            
            async with session_scope() as db:
                for opp in opportunities:
                    if not opp: continue
                    await ImprovementRepository.create(
                        db,
                        title=f"AUTO-EVOLVE: {opp.get('title')}",
                        description=opp.get('description'),
                        source_type="cognitive_memory",
                        severity=opp.get('severity', 'medium'),
                        category=opp.get('category', 'architecture'),
                        impact_score=0.7
                    )
                await db.commit()
            
            _log.info(f"[GOAL_SYNTH] {len(opportunities)} adet otonom iyileştirme fırsatı kaydedildi.")
            
        except Exception as e:
            _log.error(f"[GOAL_SYNTH] Otonom fırsat çıkarım hatası: {e}")

    def _parse_json(self, text: str) -> Optional[Dict]:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                import json
                return json.loads(match.group())
            except:
                pass
        return None

# --- Background Task Definition ---
async def start_goal_synthesis_loop():
    synthesizer = GoalSynthesizer()
    while True:
        try:
            await synthesizer.run_synthesis_cycle()
            await asyncio.sleep(3600 * 12) # 12 Saatte bir çalıştır (Daha stratejik periyot)
        except Exception as e:
            _log.error(f"[GOAL_SYNTH] Background loop error: {e}")
            await asyncio.sleep(600)
