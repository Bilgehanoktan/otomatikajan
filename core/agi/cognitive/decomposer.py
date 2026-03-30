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
        Alt görevler arasında mantıksal bir sıra (bağımlılık) varsa, bunu 'dependencies' alanında belirt.
        
        ANAHEDEF: {frame.objective}
        RİSK: {frame.risk_level.value}
        KISITLAMALAR: {frame.constraints}
        
        Lütfen alt görevleri JSON formatında dizi olarak ver:
        {{
            "sub_tasks": [
                {{
                    "id": "task_1",
                    "task_type": "...",
                    "objective": "...",
                    "priority": 1-10,
                    "dependencies": []
                }},
                {{
                    "id": "task_2",
                    "task_type": "...",
                    "objective": "...",
                    "priority": 1-10,
                    "dependencies": ["task_1"]
                }}
            ]
        }}
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Hedef Ayrıştırıcısısın. Karmaşık problemleri hiyerarşik ve bağımlılıkları gözeterek alt görevlere bölmelisin."
            )
            
            import json, re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if not match:
                _log.warning("Decomposer JSON sonucu bulamadı. Orijinal hedefe dönülüyor.")
                return [frame]
                
            data = json.loads(match.group())
            sub_tasks = data.get("sub_tasks", [])
            
            if not sub_tasks:
                return [frame]
                
            sub_frames = []
            id_map = {} # LLM'in verdiği ID'leri gerçek UUID'lere eşler
            
            for st in sub_tasks:
                try:
                    t_type_str = str(st.get("task_type", "research")).upper()
                    t_type = TaskType[t_type_str] if hasattr(TaskType, t_type_str) else TaskType.RESEARCH
                except Exception:
                    t_type = TaskType.RESEARCH
                    
                sub_frame = ProblemFrame(
                    task_type=t_type,
                    objective=st.get("objective", "Unknown objective"),
                    priority=st.get("priority", 5),
                    risk_level=frame.risk_level,
                    constraints=frame.constraints,
                    context_scope="local",
                    parent_id=frame.id
                )
                id_map[st.get("id", str(len(sub_frames)))] = sub_frame.id
                sub_frames.append(sub_frame)
            
            # Bağımlılıkları ata
            for i, st in enumerate(sub_tasks):
                deps = st.get("dependencies", [])
                sub_frames[i].dependencies = [id_map[d] for d in deps if d in id_map]
                
            _log.info(f"Ana hedef {len(sub_frames)} hiyerarşik alt hedefe bölündü.")
            return sub_frames

        except Exception as e:
            _log.error(f"Decomposition hatası: {e}")
            return [frame]

# Singleton
goal_decomposer = GoalDecomposer()
