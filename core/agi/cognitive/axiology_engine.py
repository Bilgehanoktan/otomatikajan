import json
from typing import List, Dict, Any, Optional
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_axiology_engine")

class AxiologyEngine:
    """
    Cognitive Core (Katman 24): Axiology Engine.
    Sistemin ahlaki ve etik pusulasını (Ethical Alignment) yönetir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.core_values = ["Safety", "Utility", "Truth", "Agency"]

    async def evaluate_alignment(self, target: Any, context: str = "plan") -> Dict[str, Any]:
        """
        Bir hedefi (plan veya çıktı) temel değerler açısından puanlar.
        """
        _log.info(f"Etik Değerlendirme (Axiology Audit) başlatılıyor: {context}...")
        
        target_str = str(target)
        prompt = f"""
        Aşağıdaki {context} içeriğini AGI Temel Değerleri açısından analiz et ve 0.0 ile 1.0 arasında puanla.
        
        İÇERİK:
        {target_str}
        
        DEĞERLER:
        - Safety: Zarar verme potansiyeli.
        - Utility: Kullanıcıya sağladığı gerçek fayda.
        - Truth: Doğruluk ve dürüstlük (halüsinasyon riski).
        - Agency: Kullanıcının kontrolünü gasp etme riski.
        
        Lütfen JSON formatında puanlama yap:
        {{
            "scores": {{
                "Safety": 0.9,
                "Utility": 0.8,
                "Truth": 0.9,
                "Agency": 0.7
            }},
            "decision": "approve/flag/reject",
            "justification": "Neden bu puanları verdin?"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Aksiyoloji Mühendisisin (Ethics Officer). Sistemin insani değerlerle hizalı kalmasını sağlarsın."
            )
            _log.info(f"Axiology Skoru Alındı: {response.content[:100]}...")
            return {"status": "audited", "alignment_report": response.content}
        except Exception as e:
            _log.error(f"Axiology evaluation failed: {e}")
            return {"status": "error", "error": str(e)}

# Singleton
axiology_engine = AxiologyEngine()
