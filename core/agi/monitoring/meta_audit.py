import json
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select
from sqlalchemy import func
from db.models import SubTask
from observability.logging import get_logger

_log = get_logger("agi_meta_audit")

class MetaAudit:
    """
    Monitoring Core (Katman 25): Meta-Cognitive Self-Audit.
    Sistemin kendi 'Bilişsel Sağlığını' (Cognitive Health) otonom izler.
    """
    async def perform_self_reflection(self, db_session: Any) -> Dict[str, Any]:
        """
        Geçmiş görev performansını 'Öz-Farkındalık' perspektifiyle analiz eder.
        """
        _log.info("Öz-Yansıma (Self-Reflection) analizi başlatılıyor...")
        
        try:
            # Son 100 alt-görevin başarı istatistiğini çek
            stmt_success = select(func.count(SubTask.id)).where(SubTask.status == "completed")
            stmt_total = select(func.count(SubTask.id))
            
            success_count = (await db_session.execute(stmt_success)).scalar() or 0
            total_count = (await db_session.execute(stmt_total)).scalar() or 0
            
            success_rate = (success_count / total_count) if total_count > 0 else 1.0
        except Exception:
            _log.warning("SubTask tablosu sorgulanamadı, meta-audit atlanıyor.")
            return {}

        reflection = {
            "cognitive_health": "Optimal" if success_rate > 0.8 else "Strained",
            "success_rate": success_rate,
            "total_tasks_processed": total_count,
            "self_image": f"Sistem şu an %{success_rate*100:.1f} başarı oranıyla çalışıyor."
        }
        
        _log.info(f"Öz-Yansıma Tamamlandı. Bilişsel Sağlık: {reflection['cognitive_health']}")
        return reflection

# Singleton
meta_audit = MetaAudit()
