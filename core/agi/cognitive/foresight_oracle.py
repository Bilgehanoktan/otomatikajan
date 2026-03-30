import json
from typing import List, Dict, Any, Optional
from llm.model_orchestrator import ModelOrchestrator
from core.agi.schemas import PlanProposal
from observability.logging import get_logger

_log = get_logger("agi_foresight_oracle")

class ForesightOracle:
    """
    Cognitive Core (Katman 23): Foresight Oracle.
    Planları eylemden önce zihinsel olarak simüle eder (Mental Simulation).
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def simulate_plan(self, plan: PlanProposal) -> List[Dict[str, Any]]:
        """
        Bir planın adımlarını simüle eder ve olası riskleri saptar.
        Geçmiş hatalardan (Anti-Patterns) ders çıkararak simülasyonu derinleştirir. [Katman 23]
        """
        import dataclasses
        from db.session import session_scope
        from db.models import ImprovementOpportunity
        from sqlalchemy import select
        
        _log.info(f"Yansımalı Plan Simülasyonu (Reflective Mental Simulation) başlatılıyor...")
        
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
            _log.warning(f"Anti-Pattern verisi alınamadı (devam ediliyor): {e}")

        anti_pattern_context = "\n".join(anti_patterns) if anti_patterns else "Henüz kayıtlı yüksek öncelikli hata deseni bulunamadı."

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
                    "impact": "Sisteme etkisi",
                    "recurring_pattern_match": true/false
                }}
            ]
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Öngörü Kehanetisin (Foresight Oracle). Geçmiş hatalardan ders çıkarır, eylemlerin gizli risklerini henüz gerçekleşmeden görürsün."
            )
            # Parse (simulated for now)
            _log.info(f"Simülasyon Tamamlandı, Riskler Saptandı: {response.content[:100]}...")
            return [{"id": "foresight_risk", "raw": response.content}]
        except Exception as e:
            _log.error(f"Foresight simulation failed: {e}")
            return []

# Singleton
foresight_oracle = ForesightOracle()
