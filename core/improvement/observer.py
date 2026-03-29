import uuid
from typing import List, Dict
from memory.watchdog import watchdog
from observability.logging import get_logger
from db.session import AsyncSessionLocal
from db.repository import ProjectRepository

logger = get_logger("improvement.observer")

class ImprovementObserver:
    def __init__(self):
        self.threshold_score = 0.6
        self.min_occurrences = 3

    async def scan_for_issues(self) -> List[Dict]:
        """Sistemi tarar ve iyileştirme adaylarını döner."""
        issues = []
        
        # 1. Tekrarlanan Kritik Hataları Ara (Vektör Bellek Üzerinden)
        try:
            patterns = await watchdog.search_events("tekrarlanan hata anomali timeout rate limit", top_k=10)
            
            # Basit kümeleme (Ajan bazlı)
            agent_stats = {}
            for event in patterns:
                aid = event.get("agent_id")
                if aid:
                    agent_stats[aid] = agent_stats.get(aid, 0) + 1
                
            for aid, count in agent_stats.items():
                if count >= self.min_occurrences:
                    issues.append({
                        "type": "reliability",
                        "agent_id": aid,
                        "reason": f"Son 10 olayda {count} kez hata tespit edildi.",
                        "evidence": [e["body"] for e in patterns if e.get("agent_id") == aid]
                    })
        except Exception as e:
            logger.error(f"Watchdog scan failed: {e}")

        # 2. Veritabanından Son Proje Hatalarını Tara (Faz 12 Hardening)
        try:
            async with AsyncSessionLocal() as db:
                recent_failures = await ProjectRepository.list_recent(db, limit=20, status="error")
                if len(recent_failures) >= 1:
                    # Hataları ajan bazlı grupla
                    for proj in recent_failures:
                        issues.append({
                            "type": "agent_failure",
                            "agent_id": proj.assigned_agent or "system",
                            "reason": f"Proje '{proj.title}' hatayla sonuclandi. Hata: {proj.error_detail[:200]}",
                            "evidence": {
                                "project_id": str(proj.id),
                                "error_detail": proj.error_detail,
                                "context": proj.description
                            }
                        })
        except Exception as e:
            logger.error(f"DB Project failure scan failed: {e}")
        
        return issues

observer = ImprovementObserver()
