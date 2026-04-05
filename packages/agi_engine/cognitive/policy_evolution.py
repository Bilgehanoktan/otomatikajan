import asyncio
import uuid
import json
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from observability.logging import get_logger
from core.agi.operational.velocity_engine import EngineResult
from packages.orchestration.governance.policy_engine import policy_engine, AutomationLevel
from llm.model_orchestrator import ModelOrchestrator
from db.session import session_scope
from db.repository import EventLogRepository
from packages.orchestration.agi.schemas import ActionRecord
from core.agi.cognitive.metacognitive_auditor import ReflectionCortex

_log = get_logger("policy_evolution")

class PolicyEvolutionEngine:
    """
    Sistemin operasyonel politikalarını (AutomationLevel, Risk thresholds vb.) 
    gerçek performans verilerine göre evrimleştiren 'Metakognitif' motor.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.policy_engine = policy_engine
        self.min_sample_size = 5  # Politika değişikliği için gereken minimum eylem sayısı
        self.success_threshold = 0.9 # %90 başarı oranı altındakilerde otomasyonu düşür veya izle
        self.diagnostic = ReflectionCortex(model_orch=self.model_orch)

    async def run_evolution_cycle(self, days: int = 1):
        """
        Son N gündeki performans verilerini analiz eder ve 
        politika güncellemeleri önerir/uygular.
        """
        _log.info(f"[EVOLUTION] Politika evrim döngüsü başlatıldı (Son {days} gün)")
        
        # 1. Veri Toplama (Performance Mining)
        stats = await self._gather_performance_stats(days)
        if not stats:
            _log.info("[EVOLUTION] Analiz edilecek yeterli veri bulunamadı.")
            return

        # 2. LLM Bazlı Analiz ve Sentez
        evolution_proposals = await self._synthesize_policy_adjustments(stats)
        
        # 3. Politikaları Uygulama
        for proposal in evolution_proposals:
            await self._apply_evolution_proposal(proposal)

    async def _gather_performance_stats(self, days: int) -> Dict[str, Dict[str, Any]]:
        """
        SkillExecutionLog'dan ajan/modül bazlı istatistikleri toplar.
        """
        stats = {}
        # Not: SkillLogRepository.get_all_recent gibi bir metodumuz yok, 
        # şimdilik mock veya session_scope ile manuel query yapmamız gerekebilir.
        # Basitlik için şimdilik global bir analiz simüle ediyoruz.
        
        # Gerçek uygulamada SQLAlchemy 'group_by' sorgusu yapılmalı.
        _log.debug("[EVOLUTION] Performans verileri madenleniyor...")
        
        # Faz 21: Bilişsel teşhis katmanından gerçek verileri al
        async with session_scope() as db:
            agent_stats = await self.diagnostic._get_agent_stats(db)
            
        return {"agent_performance": agent_stats}

    async def _synthesize_policy_adjustments(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Toplanan verileri LLM'e sunar ve 'Metakognitif' öneriler alır.
        """
        if not stats:
            # Test amaçlı manuel bir 'Self-Drift' denetimi yapalım (Kendi kodumuzu analiz et)
            return await self._perform_self_audit()

        prompt = f"""
        Aşağıdaki sistem performans verilerini analiz et ve 'Policy Engine' için 
        otomasyon seviyesi (AutomationLevel) veya risk eşiği (Threshold) 
        güncelleme önerileri oluştur.
        
        PERFORMANS VERİLERİ:
        {json.dumps(stats, indent=2)}
        
        MEVCUT POLİTİKALAR:
        {json.dumps(policy_engine.thresholds, indent=2)}
        
        Format:
        [
            {{"action": "update_threshold", "key": "confidence_min", "value": 65, "reason": "..."}},
            {{"action": "elevate_module", "module": "ui/", "to_level": "AUTO_MERGE", "reason": "..."}}
        ]
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="strategist",
                prompt=prompt,
                system_prompt="Sen bir AGI Stratejistisin. Sistemin operasyonel verimliliğini ve güvenliğini optimize edersin."
            )
            # JSON Parse — LLM listesi çıkar
            match = re.search(r'\[.*?\]', response.content, re.DOTALL)
            if match:
                proposals = json.loads(match.group())
                if isinstance(proposals, list):
                    _log.info(f"[EVOLUTION] {len(proposals)} politika önerisi üretildi.")
                    return proposals
            _log.warning("[EVOLUTION] LLM yanıtı geçerli JSON listesi içermiyor. Boş döndürülüyor.")
            return []
        except Exception as e:
            _log.error(f"[EVOLUTION] Sentez hatası: {e}")
            return []

    async def _perform_self_audit(self) -> List[Dict[str, Any]]:
        """
        Veri azlığında sistemin genel sağlık durumuna göre 'Hızlı Güvenlik' ayarı yapar.
        """
        _log.info("[EVOLUTION] Veri azlığı nedeniyle Self-Audit moduna geçildi.")
        # Örnek: Eğer son 24 saatte hata logları arttıysa confidence_min threshold'u yükselt.
        return [
            {
                "action": "update_threshold",
                "key": "confidence_min",
                "value": 65,
                "reason": "Genel sistem stabilitesi için güvenlik marjı artırılıyor."
            }
        ]

    async def _apply_evolution_proposal(self, proposal: Dict[str, Any]):
        """
        Önerilen evrimi PolicyEngine'e uygular ve loglar.
        """
        _log.warning(f"[EVOLUTION] Politika Güncelleniyor: {proposal.get('reason')}")
        
        update_data = {}
        if proposal["action"] == "update_threshold":
            update_data["thresholds"] = {proposal["key"]: proposal["value"]}
        
        elif proposal["action"] == "elevate_module":
            # Modül bazlı özel politikalara (Learned Policies) eklenecek
            pass 

        policy_engine.evolve_policy(update_data)
        
        # Event Bus'a bildir
        try:
            async with session_scope() as db:
                await EventLogRepository.write(
                    db,
                    event_type="policy_evolved",
                    severity="warning",
                    phase="metacognition",
                    message=f"Politika Otonom Güncellendi: {proposal.get('reason')}",
                    payload=proposal
                )
        except Exception as e:
            _log.warning(f"[EVOLUTION] Event log yazılamadı: {e}")

# --- Background Task Definition ---
async def start_policy_evolution_loop():
    engine = PolicyEvolutionEngine()
    while True:
        try:
            await engine.run_evolution_cycle()
            await asyncio.sleep(3600 * 6) # 6 Saatte bir çalıştır
        except Exception as e:
            _log.error(f"[EVOLUTION] Background loop error: {e}")
            await asyncio.sleep(300)
