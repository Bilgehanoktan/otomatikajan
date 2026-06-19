import json
from typing import List, Dict, Any, Optional
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

_log = get_logger("agi_teleology_engine")

class TeleologyEngine:
    """
    Cognitive Core (Katman 26): Teleology Engine.
    Sistemin kendi 'Amacını' (Mission Synthesis) otonom olarak belirler.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def synthesize_missions(self, learned_wisdom: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Öğrenilen bilgi ve yeteneklere dayanarak yeni 'Epics' (Misyonlar) üretir.
        """
        _log.info("Misyon Sentezi (Mission Synthesis) başlatılıyor...")
        
        wisdom_summary = str(learned_wisdom)[:2000] # Limit context
        
        prompt = f"""
        Aşağıdaki 'Öğrenilmiş Bilgelik' (Learned Wisdom) özetini analiz et.
        Sistemin şu anki kapasitesine dayanarak, kendi kendine başlatabileceği 2 adet 'Stratejik Misyon' (Epic) öner.
        
        BİLGELİK ÖZETİ:
        {wisdom_summary}
        
        Lütfen JSON formatında döndür:
        [
            {{
                "title": "Misyon Başlığı",
                "rationale": "Neden bu misyonu seçtin?",
                "complexity": "High/Medium",
                "initial_steps": ["Adım 1", "Adım 2"]
            }}
        ]
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Stratejistisin. Sistemin evrimsel hedeflerini saptar ve uzun vadeli otonom projeler başlatırsın."
            )
            _log.info(f"Otonom Misyonlar Sentezlendi: {response.content[:100]}...")
            # Not: Gerçekte JSON parse edilip Epic tablosuna yazılır.
            return [{"status": "synthesized", "raw_proposal": response.content}]
        except Exception as e:
            _log.error(f"Teleology synthesis failed: {e}")
            return []

# Singleton
teleology_engine = TeleologyEngine()
