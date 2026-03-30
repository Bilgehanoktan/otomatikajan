from typing import List, Optional, Dict, Any
from core.agi.schemas import ProblemFrame, TaskType, RiskLevel
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_decomposer")

class GoalDecomposer:
    """
    Cognitive Core (Katman 3): Hierarchical Agency.
    Karmaşık hedefleri otonom olarak alt görevlere (sub-tasking) böler.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def break_down(self, frame: ProblemFrame) -> List[ProblemFrame]:
        """
        Hevdef çok kapsamlıysa, onu alt görevlere böler.
        """
        # Hız ve maliyet optimizasyonu: Sadece yüksek riskli veya 
        # karmaşık tipleri (fix, research) bölmeye çalış.
        if frame.task_type not in [TaskType.FIX, TaskType.RESEARCH] and frame.priority < 7:
            return [frame]

        _log.info(f"Hedef Ayrıştırılıyor (Decomposition): {frame.objective[:50]}...")
        
        prompt = f"""
        Aşağıdaki karmaşık hedefi otonom olarak 2-4 adet alt göreve (sub-task) böl.
        
        ANAHEDEF: {frame.objective}
        RİSK: {frame.risk_level.value}
        KISITLAMALAR: {frame.constraints}
        
        Lütfen alt görevleri JSON formatında dizi olarak ver:
        {{
            "sub_tasks": [
                {{
                    "task_type": "...",
                    "objective": "...",
                    "priority": 1-10
                }}
            ]
        }}
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Hedef Ayrıştırıcısısın. Karmaşık problemleri daha küçük, yönetilebilir alt görevlere bölmelisin."
            )
            
            # TODO: Gerçek bir parsing ve sub-frame üretimi.
            # Şimdilik ana görevi döndür (fazla rekürsiyonu önlemek için).
            return [frame]

        except Exception as e:
            _log.error(f"Decomposition hatası: {e}")
            return [frame]

# Singleton
goal_decomposer = GoalDecomposer()
