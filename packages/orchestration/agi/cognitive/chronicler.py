import json
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select
from packages.persistence.models import Project, SubTask
from packages.observability.logging import get_logger

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

    async def record_provenance_structured(self, action: str, component: str, reason: str, change_summary: str, risk_mitigation: str, verification: str, affective_state: Optional[Dict[str, Any]] = None):
        """
        Otonom iyileştirme kararlarını makinece okunabilir JSON formatında kaydeder.
        Faz 12.3: Duygusal bağlam (affective_state) desteği eklendi.
        """
        import os
        import json
        from datetime import datetime, timezone
        
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        json_file = os.path.join(root, "PROVENANCE.json")
        md_file = os.path.join(root, "PROVENANCE.md")
        
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "12.3-A",
            "action": action,
            "component": component,
            "reason": reason,
            "change_summary": change_summary,
            "risk_mitigation": risk_mitigation,
            "verification": verification,
            "affective_context": affective_state # Duygusal hafıza
        }
        
        # 1. MD Log (İnsan için)
        log_entry = f"## [{data['timestamp']}] {action}\n"
        log_entry += f"- **Component**: `{component}`\n"
        log_entry += f"- **Reasoning**: {reason}\n"
        log_entry += f"- **Summary**: {change_summary}\n"
        log_entry += f"- **Mitigation**: {risk_mitigation}\n"
        log_entry += f"- **Verification**: {verification}\n\n"
        
        try:
            with open(md_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            _log.error(f"MD Provenance write failed: {e}")

        # 2. JSON Store (Makine/AGI Hafızası için)
        records = []
        try:
            if os.path.exists(json_file):
                with open(json_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            
            records.append(data)
            # Sadece son 100 kaydı tut (Hafıza şişmesini önle)
            records = records[-100:]
            
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            _log.error(f"JSON Provenance write failed: {e}")

    async def get_recent_provenance(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Makine dostu formatta son otonom kararları döner."""
        import os
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        json_file = os.path.join(root, "PROVENANCE.json")
        
        if not os.path.exists(json_file):
            return []
            
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                records = json.load(f)
            return records[-limit:]
        except Exception as e:
            _log.warning(f"Failed to read provenance memory: {e}")
            return []

# Singleton
chronicler = Chronicler()
