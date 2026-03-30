import asyncio
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from db.session import session_scope
from db.repository import ImprovementRepository, ProjectRepository, EventLogRepository
from core.agi.schemas import SourceType

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
            from core.agi.cognitive.nexus_orchestrator import nexus_orchestrator
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
