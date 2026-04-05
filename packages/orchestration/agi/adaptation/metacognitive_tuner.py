import json
from typing import List, Dict, Any, Optional
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.observability.logging import get_logger

_log = get_logger("agi_metacognitive_tuner")

class MetacognitiveTuner:
    """
    Adaptation Core (Katman 25): Metacognitive Tuner.
    Öz-yansıma verileriyle sistemin bilişsel modunu (Modality) otonom ayarlar.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def tune_metacognition(self, reflection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sistemin kendi durumuna dair 'Meta-Düşünce' (Meta-Thought) üretir.
        """
        if not reflection:
            return {"status": "skipped", "reason": "No self-reflection data."}
            
        _log.info("Meta-Bilişsel Ayarlama (Metacognitive Tuning) başlatılıyor...")
        
        prompt = f"""
        Aşağıdaki sistemsel öz-yansımayı (Self-Reflection) değerlendir.
        Gelecekteki görevlerde bu "öz-farkındalığı" yansıtacak bir "Meta-Prompt" (Öz-Yönerge) üret.
        
        YANSIMA:
        {json.dumps(reflection, indent=2)}
        
        Lütfen sistemin bir sonraki göreve nasıl yaklaşması gerektiğini JSON olarak döndür:
        {{
            "suggested_modality": "Simplified / Deep / Alert / Analytical",
            "meta_prompt": "Bu göreve yaklaşırken şunun farkındayım: ...",
            "reasoning": "Düşünce sürecin."
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Öz-Farkındalık Mühendisisin. Sistemin kapasitesini ve limitlerini otonom olarak yönetirsin."
            )
            _log.info(f"Meta-Tuning Önerisi Alındı: {response.content[:100]}...")
            return {"status": "tuned", "metacognition": response.content}
        except Exception as e:
            _log.error(f"Metacognitive tuning failed: {e}")
            return {"status": "error", "error": str(e)}

# Singleton
metacognitive_tuner = MetacognitiveTuner()
