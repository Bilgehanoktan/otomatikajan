import json
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select
from db.models import Project, SubTask
from observability.logging import get_logger

_log = get_logger("agi_chronicler")

class Chronicler:
    """
    Cognitive Core (Katman 21): Chronicler.
    Sistemin zaman bazlı tecrübesini (Temporal Experience) modeller.
    """
    async def analyze_temporal_patterns(self, db_session: Any) -> Dict[str, Any]:
        """
        Geçmiş görevlerin sürelerini ve verimliliğini analiz eder.
        """
        _log.info("Zaman Analizi (Temporal Analysis) başlatılıyor...")
        
        try:
            # Son 20 tamamlanmış görevi çek
            stmt = select(Project).where(Project.completed_at != None).order_by(Project.completed_at.desc()).limit(20)
            result = await db_session.execute(stmt)
            projects = result.scalars().all()
        except Exception:
            _log.warning("Project tablosu sorgulanamadı, zaman analizi atlanıyor.")
            return {}

        if not projects:
            return {}

        stats: List[Dict[str, Any]] = []
        for p in projects:
            if p.started_at and p.completed_at:
                duration = (p.completed_at - p.started_at).total_seconds()
                stats.append({
                    "id": str(p.id),
                    "title": p.title,
                    "duration_s": float(duration),
                    "status": p.status.value if hasattr(p.status, 'value') else str(p.status)
                })
        
        # Basit istatistiksel özet
        total_d: float = sum(float(s["duration_s"]) for s in stats)
        avg_duration = total_d / len(stats) if stats else 0.0
        
        recent_stats = []
        for i, st in enumerate(stats):
            if i < 5:
                recent_stats.append(st)
        
        analysis = {
            "avg_project_duration_s": avg_duration,
            "sample_size": len(stats),
            "fastest_completion": min([float(s["duration_s"]) for s in stats]) if stats else 0.0,
            "slowest_completion": max([float(s["duration_s"]) for s in stats]) if stats else 0.0,
            "recent_history": recent_stats
        }
        
        _log.info(f"Zaman Analizi Tamamlandı. Ortalama Süre: {avg_duration:.2f}s")
        return analysis

# Singleton
chronicler = Chronicler()
