import json
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.future import select
from packages.persistence.models import TaskLog
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.observability.logging import get_logger

_log = get_logger("agi_pathogen_detector")

class PathogenDetector:
    """
    Monitoring Core (Katman 19): Pathogen Detection.
    Sistemdeki tekrarlayan hata desenlerini (Pathogens) analiz eder.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def detect_pathogens(self, db_session: Any = None, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Son hataları analiz eder ve 'Patojenik' (tekrarlayan) desenleri bulur.
        """
        _log.info(f"Patojen Taraması (Pathogen Detection) başlatılıyor... (file_path={file_path})")
        
        # 1. Eğer dosya yolu verildiyse dosyayı analiz et, yoksa DB loglarını
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()[:5000]
            log_summary = [{"event": "file_analysis", "message": content, "agent": "pathogen_detector"}]
        elif db_session:
            # Son hataları çek (Level='error' or 'critical')
            try:
                stmt = select(TaskLog).where(TaskLog.level.in_(["error", "critical"])).limit(50)
                result = await db_session.execute(stmt)
                logs = result.scalars().all()
                log_summary = [{"event": l.event, "message": l.message, "agent": l.agent_id} for l in logs]
            except Exception:
                _log.warning("TaskLog sorgulanamadı, patojen taraması atlanıyor.")
                return []
        else:
            _log.warning("Patojen taraması için ne DB session ne de dosya yolu verildi.")
            return []
            
        if not log_summary:
            return []
        
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
            # LLM cevabını parse et (JSON extractor)
            data = self._parse_json(response.content)
            if data and isinstance(data, list):
                _log.info(f"Patojenler Tespit Edildi: {len(data)} tane.")
                return data
            elif data and isinstance(data, dict):
                 return [data]
            
            _log.warning("Patojen JSON ayrıştırılamadı, raw dönülüyor.")
            return [{"id": "detected_pathogen", "raw": response.content}]
        except Exception as e:
            _log.error(f"Pathogen detection error: {e}")
            return []

    def _parse_json(self, text: str) -> Optional[Union[Dict, List]]:
        import re
        match = re.search(r'\[.*\]|\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return None

# Singleton
pathogen_detector = PathogenDetector()
