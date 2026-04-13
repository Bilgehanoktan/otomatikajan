import json
import os
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select
from libs.db.models import SubTask
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

_log = get_logger("agi_specialist_forge")

class SpecialistForge:
    """
    Learning Core (Katman 22): Specialist Forge.
    Başarılı desenlerden yeni uzman ajan rolleri üretir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None, roles_path: str = "agents/dynamic_agents.json"):
        self.model_orch = model_orch or ModelOrchestrator()
        self.roles_path = roles_path

    async def forge_new_specialists(self, db_session: Any) -> List[Dict[str, Any]]:
        """
        Başarılı alt-görevleri analiz eder ve yeni roller sentezler.
        """
        _log.info("Uzman Sentezi (Specialist Forge) başlatılıyor...")
        
        try:
            # 1. Başarılı desenleri çek (High quality score >= 0.9)
            best_stmt = select(SubTask).where(SubTask.quality_score >= 0.9).order_by(SubTask.created_at.desc()).limit(20)
            best_res = await db_session.execute(best_stmt)
            best_tasks = best_res.scalars().all()
            
            # 2. Hatalı desenleri çek (AGI Gap: Failure Learning)
            fail_stmt = select(SubTask).where(SubTask.quality_score < 0.5).order_by(SubTask.created_at.desc()).limit(20)
            fail_res = await db_session.execute(fail_stmt)
            fail_tasks = fail_res.scalars().all()
            
        except Exception as e:
            _log.warning(f"SubTask tablosu sorgulanamadı ({e}), uzman sentezi kısıtlı başlatılıyor.")
            return []

        if not best_tasks:
            return []

        task_patterns = [{"agent": t.agent_id, "prompt": t.prompt[:200], "score": t.quality_score} for t in best_tasks]
        failure_lessons = [{"agent": t.agent_id, "error": t.response[:200] if "error" in t.response.lower() else "Sub-optimal result", "score": t.quality_score} for t in fail_tasks]
        
        prompt = f"""
        Aşağıdaki desenleri analiz et. Bir AGI mimarı olarak, sistemin hem BAŞARILARINDAN hem de HATALARINDAN öğrenen yeni bir 'Uzman Ajan' sentezle.
        
        BAŞARILI DESENLER (Kopya edilecek pratikler):
        {json.dumps(task_patterns, indent=2)}
        
        HATALI DESENLER VE ÖĞRENİLEN DERSLER (Kaçınılacak pratikler - INHIBITION):
        {json.dumps(failure_lessons, indent=2)}
        
        Lüften YENİ rol için JSON formatında tanım yap. 'system_prompt' içerisinde mutlaka geçmiş hatalardan koruyacak 'Constraint'lere de yer ver:
        {{
            "role_id": "specialist_name",
            "title": "Uzmanlık Başlığı",
            "system_prompt": "Bu uzmanın otonom davranış kuralları ve kaçınması gereken hata paternleri...",
            "capabilities": ["cap1", "cap2"]
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Uzman Sentezleyicisisin (Specialist Forge). En iyi performans gösteren desenlerden süper-uzmanlar yaratırsın."
            )
            import re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if not match: return []
            
            new_role = json.loads(match.group())
            role_id = new_role.get("role_id", "auto_specialist_" + str(uuid.uuid4())[:8])
            
            # Map forge schema to AgentRegistry schema
            ecc_agent = {
                "id": role_id,
                "name": new_role.get("title", "Otonom Uzman"),
                "emoji": "🛠️",
                "role": "/".join(new_role.get("capabilities", ["AI Specialist"])),
                "system_prompt": new_role.get("system_prompt", "")
            }
            
            # Persist to dynamic_agents.json
            current_agents = []
            if os.path.exists(self.roles_path):
                with open(self.roles_path, "r", encoding="utf-8") as f:
                    try:
                        current_agents = json.load(f)
                    except Exception:
                        current_agents = []
            
            # Update or Append
            existing_idx = next((i for i, a in enumerate(current_agents) if a["id"] == role_id), None)
            if existing_idx is not None:
                current_agents[existing_idx] = ecc_agent
            else:
                current_agents.append(ecc_agent)
                
            with open(self.roles_path, "w", encoding="utf-8") as f:
                json.dump(current_agents, f, indent=2)
                
            _log.info(f"[FORGE] YENİ UZMAN SENTEZLENDİ VE KAYDEDİLDİ: {role_id}")
            return [ecc_agent]
        except Exception as e:
            _log.error(f"Specialist forge error: {e}")
            return []

# Singleton
specialist_forge = SpecialistForge()
