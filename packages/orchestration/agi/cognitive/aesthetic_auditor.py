import os
from typing import Dict, Any, Optional
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.observability.logging import get_logger

_log = get_logger("agi_aesthetic_auditor")

class AestheticAuditor:
    """
    Cognitive Core (Katman 18): Aesthetic Reflection.
    Sistemin kendi görsel kalitesini denetlediği ve 'SOTA' (State of the Art) standartlarına göre puanladığı üst katman.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None, css_path: str = "frontend/src/index.css"):
        self.model_orch = model_orch or ModelOrchestrator()
        self.css_path = css_path

    async def audit_aesthetics(self) -> Dict[str, Any]:
        """
        Sistemin CSS yapısını analiz eder ve estetik sağlığını (Aesthetic Health) skorlar.
        """
        _log.info("Estetik Denetim (Visual Audit) balatlyor...")
        
        css_content = ""
        if os.path.exists(self.css_path):
            with open(self.css_path, "r", encoding="utf-8") as f:
                css_content = f.read()[:5000] # İlk 5000 karakteri analiz et (LLM limit)
        
        prompt = f"""
        Aşağıdaki CSS kodunu modern 'Premium Web Design' (Glassmorphism, Dark Mode, Micro-animations) standartlarına göre denetle.
        
        CSS:
        {css_content}
        
        Lütfen şunları döndür:
        1. Aesthetic Score (0-100)
        2. Aesthetic Debt (Neler eksik? Örn: 'Gradients are missing', 'Blur effects missing')
        3. Önerilen kod parçası.
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="ui_designer",
                prompt=prompt,
                system_prompt="Sen bir Premium AGI Estetik Denetçisisin (UI/UX Auditor). Yanıtlarını JSON formatında ver: {'score': int, 'debt': [], 'suggestion': ''}"
            )
            
            # JSON Parse (Helper metodu Pathogen ile aynı mantıkta buraya da eklenebilir veya generic bir yere alınabilir)
            data = self._parse_json(response.content)
            
            _log.info(f"Visual Audit Tamamlandı. Score: {data.get('score') if data else 'unknown'}")
            
            return {
                "status": "completed",
                "score": data.get("score", 70) if data else 70,
                "debt": data.get("debt", []) if data else [],
                "suggestion": data.get("suggestion", "") if data else response.content,
                "raw_feedback": response.content if not data else None,
                "timestamp": os.path.getmtime(self.css_path) if os.path.exists(self.css_path) else 0
            }
            
        except Exception as e:
            _log.error(f"Aesthetic audit failed: {e}")
            return {"status": "failed", "error": str(e)}

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        import re
        import json
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return None

# Singleton
aesthetic_auditor = AestheticAuditor()
