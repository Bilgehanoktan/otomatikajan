import json
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select
from db.models import TaskLog
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_pathogen_detector")

class PathogenDetector:
    """
    Monitoring Core (Katman 19): Pathogen Detection.
    Sistemdeki tekrarlayan hata desenlerini (Pathogens) analiz eder.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def detect_pathogens(self, db_session: Any) -> List[Dict[str, Any]]:
        """
        Son hataları analiz eder ve 'Patojenik' (tekrarlayan) desenleri bulur.
        """
        _log.info("Patojen Taraması (Pathogen Detection) başlatılıyor...")
        
        # 1. Son hataları çek (Level='error' or 'critical')
        try:
            stmt = select(TaskLog).where(TaskLog.level.in_(["error", "critical"])).limit(50)
            result = await db_session.execute(stmt)
            logs = result.scalars().all()
        except Exception:
            _log.warning("TaskLog sorgulanamadı, patojen taraması atlanıyor.")
            return []
            
        if not logs:
            return []
            
        log_summary = [{"event": l.event, "message": l.message, "agent": l.agent_id} for l in logs]
        
        prompt = f"""
        Aşağıdaki sistem hata loglarını analiz et. 
        Tekrarlayan "Yapısal" (Structural) hata desenlerini (Pathogens) tespit et.
        Tesadüfi hataları (örn: bir kerelik network timeout) atla.
        
        LOGLAR:
        {json.dumps(log_summary, indent=2)}
        
        Lütfen tespit edilen her Patojen için JSON listesi döndür:
        {{
            "pathogen_id": "unique_id",
            "module": "hata_kaynagi_modul",
            "error_type": "hata_tipi",
            "frequency": 3,
            "description": "Neden yapısal bir hata?"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Sistem İmmunoloğusun. Yapısal zayıflıkları (hata desenleri) bulursun."
            )
            # LLM cevabını parse et (Özet olarak listeyi döndür)
            _log.info(f"Patojenler Tespit Edildi: {response.content[:100]}...")
            # TODO: Gerçek bir JSON extractor eklenebilir.
            return [{"id": "detected_pathogen", "raw": response.content}]
        except Exception as e:
            _log.error(f"Pathogen detection error: {e}")
            return []

# Singleton
pathogen_detector = PathogenDetector()
