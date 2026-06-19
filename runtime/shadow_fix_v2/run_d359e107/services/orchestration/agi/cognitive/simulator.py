import json
from typing import Optional, Dict, List, Any
from services.orchestration.agi.schemas import ExecutionPlan, ProblemFrame, RiskLevel
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

_log = get_logger("agi_simulation_engine")

class SimulationEngine:
    """
    Cognitive Core (Katman 3): Pre-Action Simulation.
    Özellikle orta/yüksek riskli planları sanal olarak simüle ederek yan etkileri öngörür.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def simulate(self, frame: ProblemFrame, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Planı zihinsel/sanal ortamda simüle eder.
        """
        if frame.risk_level == RiskLevel.LOW:
            return {"status": "skipped", "message": "Düşük riskli görev için simülasyon atlandı."}

        _log.info(f"Plan simülasyonu başlatılıyor: {plan.goal}")

        # Simülasyon istemi
        prompt = self._build_simulation_prompt(frame, plan)
        system_prompt = (
            "Sen bir AGI Simülasyon Çekirdeği (Simulation Engine) bileşenisin. "
            "Sana verilen uygulama planını, sistemin 'dünya modeli' üzerinde sanal olarak denemeli, "
            "olası yan etkileri, riskleri ve başarı ihtimalini tahmin etmelisin. "
            "Eleştirel ve 'Red Team' bakış açısıyla yaklaş."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Yanıtı analiz et (Basit metin analizi veya yapısal JSON)
            return {
                "status": "completed",
                "simulation_notes": response.content,
                "predicted_success_rate": 0.85 if "başarılı" in response.content.lower() else 0.5,
                "warnings": self._extract_warnings(response.content)
            }

        except Exception as e:
            _log.error(f"Simülasyon hatası: {e}")
            return {"status": "error", "message": str(e)}

    def _build_simulation_prompt(self, frame: ProblemFrame, plan: ExecutionPlan) -> str:
        steps_text = "\n".join([f"{i+1}. {s.action} ({s.params})" for i, s in enumerate(plan.steps)])
        return f"""
        HEDEF: {frame.objective}
        RİSK SEVİYESİ: {frame.risk_level.value}
        
        UYGULAMA PLANI:
        {steps_text}
        
        Lütfen bu planın uygulanması durumunda:
        1. Hangi dosyalar veya modüller etkilenebilir?
        2. Olası yan etkiler nelerdir? (Örn: performans kaybı, güvenlik açığı)
        3. Planın zayıf noktaları nelerdir?
        4. Başarı ihtimali nedir?
        
        Simülasyon raporunu teknik ve detaylı hazırla.
        """

    def _extract_warnings(self, content: str) -> List[str]:
        # Basit uyarı ayıklama mantığı
        warnings = []
        if "risk" in content.lower():
            warnings.append("Potansiyel risk tespit edildi.")
        if "dikkat" in content.lower():
            warnings.append("Kritik noktalar mevcut.")
        return warnings

# --- Singleton ---
simulation_engine = SimulationEngine()
