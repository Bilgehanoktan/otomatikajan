import json
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select
from db.models import SubTask
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_specialist_forge")

class SpecialistForge:
    """
    Learning Core (Katman 22): Specialist Forge.
    Başarılı desenlerden yeni uzman ajan rolleri üretir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None, roles_path: str = "core/agi/roles/specialists.json"):
        self.model_orch = model_orch or ModelOrchestrator()
        self.roles_path = roles_path

    async def forge_new_specialists(self, db_session: Any) -> List[Dict[str, Any]]:
        """
        Başarılı alt-görevleri analiz eder ve yeni roller sentezler.
        """
        _log.info("Uzman Sentezi (Specialist Forge) başlatılıyor...")
        
        try:
            # High quality score (>= 0.9) olan görevleri çek
            stmt = select(SubTask).where(SubTask.quality_score >= 0.9).limit(50)
            result = await db_session.execute(stmt)
            best_tasks = result.scalars().all()
        except Exception:
            _log.warning("SubTask tablosu sorgulanamadı, uzman sentezi atlanıyor.")
            return []

        if not best_tasks:
            return []

        task_patterns = [{"agent": t.agent_id, "prompt": t.prompt[:200], "score": t.quality_score} for t in best_tasks]
        
        prompt = f"""
        Aşağıdaki başarılı görev desenlerini analiz et. 
        Bu desenlerden yola çıkarak "Kombine Uzmanlık" gerektiren YENİ bir Ajan Rolü (Hyper-Specialist) sentezle.
        
        DESENLER:
        {json.dumps(task_patterns, indent=2)}
        
        Lütfen yeni rol için JSON formatında tanım yap:
        {{
            "role_id": "specialist_name",
            "title": "Uzmanlık Başlığı",
            "system_prompt": "Bu uzmanın otonom davranış kuralları...",
            "capabilities": ["cap1", "cap2"]
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Uzman Sentezleyicisisin (Specialist Forge). En iyi performans gösteren desenlerden süper-uzmanlar yaratırsın."
            )
            # Parse and save (simulated)
            _log.info(f"YENİ UZMAN SENTEZLENDİ: {response.content[:100]}...")
            # TODO: persist to self.roles_path
            return [{"id": "new_specialist", "raw": response.content}]
        except Exception as e:
            _log.error(f"Specialist forge error: {e}")
            return []

# Singleton
specialist_forge = SpecialistForge()
