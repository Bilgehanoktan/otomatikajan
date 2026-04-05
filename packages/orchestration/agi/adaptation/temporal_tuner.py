import json
from typing import List, Dict, Any, Optional
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_temporal_tuner")

class TemporalTuner:
    """
    Adaptation Core (Katman 21): Temporal Tuner.
    Zaman bazlı verilerle sistemin operasyonel parametrelerini optimize eder.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def tune_temporal_parameters(self, temporal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Zaman analizine dayanarak otonom optimizasyon önerileri sunar.
        """
        if not temporal_analysis:
            return {"status": "skipped", "reason": "No temporal data available."}
            
        _log.info("Zaman Parametreleri Optimize Ediliyor (Temporal Tuning)...")
        
        prompt = f"""
        Aşağıdaki sistemsel zaman analizini (Temporal Analysis) değerlendir.
        Gelecekteki görevlerin daha başarılı olması için otonom olarak 'Timeout', 'Retry' ve 'Priority' ayarları öner.
        
        ANALİZ:
        {json.dumps(temporal_analysis, indent=2)}
        
        Lütfen yeni ayarlar için JSON formatında öneri sun:
        {{
            "new_timeout_s": 300,
            "priority_logic": "dynamic",
            "reasoning": "Neden bu değişikliği önerdin?"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Zaman Mühendisisin. Sistemin operasyonel hızını ve verimliliğini optimize edersin."
            )
            # LLM önerisini parse et ve logla (Gerçekte config dosyasına veya DB'ye kaydedilebilir)
            _log.info(f"Temporal Tuning Önerisi Alındı: {response.content[:100]}...")
            return {"status": "tuned", "recommendation": response.content}
        except Exception as e:
            _log.error(f"Temporal tuning failed: {e}")
            return {"status": "error", "error": str(e)}

# Singleton
temporal_tuner = TemporalTuner()
