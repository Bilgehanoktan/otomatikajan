import logging
from typing import Optional, Tuple
from libs.llm.model_orchestrator import ModelOrchestrator

logger = logging.getLogger("services.orchestration.application.task_routing")

class TaskRouter:
    """
    Semantic Task Router — Content-aware automatic agent assignment.
    Ensures that DeerFlow roles and standard agents are selected based on task complexity.
    """
    
    ROUTING_PROMPT = """
Sistemimizdeki 5 ana yürütme modundan en uygun olanı seç.

ÖRNEKLER:
- "Fix login bug" -> deerflow_recovery
- "Research OAuth libs" -> deerflow_research
- "Audit security" -> deerflow_review
- "Implement new dashboard" -> run_project
- "Plan migration to AWS" -> deerflow_plan

MODLAR:
1. deerflow_plan: Mimari tasarım, strateji, çoklu alt görev.
2. deerflow_research: Teknik detay araştırma, repo analizi.
3. deerflow_review: Kod kalitesi, denetim, refactor önerisi.
4. deerflow_recovery: Hata giderme, incident, acil onarım.
5. run_project: Standart geliştirme döngüsü.

GÖREV: {title}
AÇIKLAMA: {description}

SADECE slug değerini (örn: deerflow_plan) döndür.
"""

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def route_task(self, title: str, description: str, workflow_template: str = "default") -> str:
        """Faz 12 Hardening: Keyword-first + LLM Fallback Routing."""
        # 0. Template-tabanlı kesin yönlendirme (Faz 12.1)
        if workflow_template == "audit":
            return "deerflow_review"
        if workflow_template == "hotfix":
            return "deerflow_recovery"
        if workflow_template == "plan":
            return "deerflow_plan"
        if workflow_template == "verify":
            return "deerflow_review"
            
        text = (title + " " + description).lower()

        # 1. Kural Tabanlı Ön Filtre (Yüksek Güven)
        if any(w in text for w in ["fix", "bug", "error", "hata", "incident", "onarım", "hotfix"]):
            return "deerflow_recovery"
        if any(w in text for w in ["audit", "review", "denetim", "refactor", "incele"]):
            return "deerflow_review"
        if any(w in text for w in ["research", "araştır", "inceleme", "analysis", "analiz"]):
            return "deerflow_research"
        if any(w in text for w in ["plan", "design", "mimari", "architecture", "strateji"]):
            return "deerflow_plan"

        # 2. LLM Bazlı Karar (Fallback)
        try:
            prompt = self.ROUTING_PROMPT.format(title=title, description=description)
            decision = await self.model_orch.generate(prompt, system_prompt="Sen sistemin trafik yöneticisisin.")
            decision = decision.strip().lower().replace('"', '').replace("'", "")

            valid_slugs = ["deerflow_plan", "deerflow_research", "deerflow_review", "deerflow_recovery", "run_project"]
            for slug in valid_slugs:
                if slug in decision:
                    return slug
            
            return "run_project"
        except Exception as e:
            logger.error(f"[ROUTING] Semantic routing failed: {e}")
            return "run_project"

# Singleton
task_router = TaskRouter()
