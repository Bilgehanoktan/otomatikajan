import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import model_orchestrator, ModelOrchestrator
from core.agi.schemas import PlanProposal

_log = get_logger("agi_foresight")

class ForesightCortex:
    """
    Cognitive Core (Katman 28): Foresight Cortex (Multiversal Mesh).
    Kararların paralel gelecek simülasyonları üzerinden alınmasını sağlar.
    'En az riskli, en yüksek öngörü' modelini hedefler.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or model_orchestrator

    async def simulate_plan(self, plan: PlanProposal) -> List[Dict[str, Any]]:
        """
        Bir planın adımlarını simüle eder ve olası riskleri saptar. (Legacy Oracle Logic)
        Geçmiş hatalardan (Anti-Patterns) ders çıkararak simülasyonu derinleştirir.
        """
        import dataclasses
        from db.session import session_scope
        from db.models import ImprovementOpportunity
        from sqlalchemy import select
        
        _log.info(f"[FORESIGHT] Yansımalı Plan Simülasyonu (Reflective Mental Simulation) başlatılıyor...")
        
        # 1. Geçmiş Hataları (Anti-Patterns) Topla
        anti_patterns = []
        try:
            async with session_scope() as db:
                result = await db.execute(
                    select(ImprovementOpportunity)
                    .where(ImprovementOpportunity.severity == "high")
                    .limit(5)
                )
                opps = result.scalars().all()
                anti_patterns = [f"- {o.title}: {o.description}" for o in opps]
        except Exception as e:
            _log.warning(f"[FORESIGHT] Anti-Pattern verisi alınamadı (devam ediliyor): {e}")

        anti_pattern_context = "\n".join(anti_patterns) if anti_patterns else "Henüz saptanmış kritik hata deseni bulunamadı."

        prompt = f"""
        Aşağıdaki uygulama planını adım adım zihninde simüle et. 
        Her adım için "Ne yanlış gidebilir?" sorusunu sor ve olası riskleri (Edge Cases) belirle.
        
        GEÇMİŞTE SAPTANAN KRİTİK HATA DESENLERİ (BUNLARDAN KAÇIN):
        {anti_pattern_context}
        
        PLAN:
        {json.dumps(dataclasses.asdict(plan), indent=2, default=str)}
        
        Lütfen saptanan riskleri JSON listesi olarak döndür:
        {{
            "predicted_risks": [
                {{
                    "step_index": 1,
                    "severity": "high/medium/low",
                    "failure_mode": "Öngörülen hata açıklaması",
                    "impact": "Sisteme etkisi"
                }}
            ]
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Öngörü Birimisin (Foresight Cortex). Geçmiş hatalardan ders çıkarır, eylemlerin gizli risklerini henüz gerçekleşmeden görürsün."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                risks = data.get("predicted_risks", [])
                _log.info(f"[FORESIGHT] Simülasyon Tamamlandı, {len(risks)} risk noktası saptandı.")
                return risks
            return []
        except Exception as e:
            _log.error(f"[FORESIGHT] Foresight simulation failed: {e}")
            return []
    
    async def simulate_parallel_futures(self, original_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Orijinal bir plan için 3 farklı paralel zaman çizelgesi (Timeline) üretir.
        Gönüllü bir simülasyon yaparak planın AGİ standartlarına uygunluğunu test eder.
        """
        _log.info(f"[FORESIGHT] '{original_plan.get('title', 'Unknown Task')}' için paralel gelecekler simüle ediliyor...")
        
        prompt = f"""
        Aşağıdaki AGI planı için 3 farklı paralel gelecek (Timeline) senaryosu üret:
        Plan Başlığı: {original_plan.get('title')}
        Plan İçeriği: {original_plan.get('content') or original_plan.get('summary')}
        
        Senaryo Tipleri:
        1. 'Conservative' (Maksimum Güvenlik, Minimum Risk)
        2. 'Balanced' (Optimum Fayda/Güvenlik Dengesi)
        3. 'Aggressive' (Hızlı Sonuç, Yüksek Risk)
        
        Her senaryo için şu alanları içeren bir JSON listesi döndür:
        - timeline_name: Senaryo adı
        - potential_outcome: Olası sonuç
        - risk_score: 0.0 - 1.0 arası risk puanı
        - utility_score: 0.0 - 1.0 arası fayda puanı
        - critical_warning: En büyük potansiyel tehlike
        """
        
        try:
            response = await model_orchestrator.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Zaman Çizgisi Simülatörüsün. Geleceği öngörmek senin görevin."
            )
            
            # JSON parsing logic improve
            match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if not match:
                # Try search for dictionary
                match = re.search(r'\{.*\}', response.content, re.DOTALL)
                
            if match:
                data = json.loads(match.group())
                timelines = data if isinstance(data, list) else data.get("timelines", [])
            else:
                _log.warning("[FORESIGHT] Simülasyon çıktısı JSON formatında bulunamadı.")
                timelines = []
                
            _log.info(f"[FORESIGHT] {len(timelines)} paralel zaman çizelgesi başarıyla üretildi.")
            return timelines
        except Exception as e:
            _log.error(f"[FORESIGHT] Gelecek simülasyonu hatası: {e}")
            return []

    async def select_optimal_timeline(self, timelines: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Üretilen senaryolar arasından en güvenli/verimli olanı seçer."""
        if not timelines:
            return None
            
        # Risk < 0.4 olanları ve Utility > 0.6 olanları seç
        optimum = sorted(timelines, key=lambda x: (x.get('utility_score', 0) - x.get('risk_score', 1)), reverse=True)
        return optimum[0] if optimum else timelines[0]

# Singleton Instance
foresight_cortex = ForesightCortex()

# Compatibility Aliases
ChronosMesh = ForesightCortex
chronos_mesh = foresight_cortex
