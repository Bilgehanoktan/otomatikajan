"""
WorldModel Katman 9.3: Task-State Graph
[FIX-9] Yürütülen görevlerin geçmişini, durumunu ve geçişlerini bir grafik
olarak modelleyerek AGI'nin görev evreni hakkında bütünsel bir anlayış
kazanmasını sağlar. "Hangi görevler başarısız oldu? Hangi ajan sıklıkla hata
üretiyor? Hangi görev türleri en çok tekrar deniyor?" gibi soruları yanıtlar.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from packages.observability.logging import get_logger

_log = get_logger("world_task_state_graph")


@dataclass
class TaskStateNode:
    """Tek bir görevin yaşam döngüsü kaydı."""
    task_id: str
    title: str
    agent_id: str = "system"
    status: str = "pending"              # pending | running | success | failed | retrying
    attempt_count: int = 0
    risk_level: str = "low"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    causal_root: Optional[str] = None   # Başarısız ise tespit edilen kök neden
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_s(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class TaskStateGraph:
    """
    WorldModel Katman 9.3: Görev Durum Grafiği.
    Tamamlanan ve devam eden görevlerin tam geçmişini tutar.
    AGI, bu bilgiyi kullanarak geçmiş hatalardan ders çıkarabilir.
    """

    _MAX_NODES = 500  # Bellek aşımını önle

    def __init__(self):
        self._nodes: Dict[str, TaskStateNode] = {}
        self._agent_failure_counts: Dict[str, int] = {}

    def register_task(self, task_id: str, title: str, agent_id: str = "system",
                      risk_level: str = "low") -> TaskStateNode:
        """Yeni bir görevi grafiğe ekler."""
        node = TaskStateNode(
            task_id=task_id,
            title=title,
            agent_id=agent_id,
            status="pending",
            risk_level=risk_level,
            started_at=datetime.now(timezone.utc)
        )
        # Kapasite yönetimi: en eski başarılı görevleri at
        if len(self._nodes) >= self._MAX_NODES:
            oldest = next(
                (k for k, v in self._nodes.items() if v.status == "success"),
                None
            )
            if oldest:
                del self._nodes[oldest]
        self._nodes[task_id] = node
        return node

    def mark_running(self, task_id: str):
        if task_id in self._nodes:
            self._nodes[task_id].status = "running"
            self._nodes[task_id].attempt_count += 1

    def mark_success(self, task_id: str):
        if task_id in self._nodes:
            n = self._nodes[task_id]
            n.status = "success"
            n.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, task_id: str, reason: str = "", causal_root: str = ""):
        if task_id in self._nodes:
            n = self._nodes[task_id]
            n.status = "failed"
            n.completed_at = datetime.now(timezone.utc)
            n.failure_reason = reason
            n.causal_root = causal_root
            # Ajan başarısızlık sayacını güncelle
            aid = n.agent_id
            self._agent_failure_counts[aid] = self._agent_failure_counts.get(aid, 0) + 1

    def get_failure_patterns(self) -> Dict[str, Any]:
        """
        Başarısızlık örüntülerini analiz eder.
        AGI bu bilgiyi plan yaparken kullanabilir.
        """
        failed = [n for n in self._nodes.values() if n.status == "failed"]
        total = len(self._nodes)
        failure_rate = len(failed) / total if total else 0.0

        # En sık başarısız olan ajan
        worst_agent = max(self._agent_failure_counts, key=self._agent_failure_counts.get) \
            if self._agent_failure_counts else None

        # En yaygın başarısızlık nedeni
        reasons = [n.failure_reason for n in failed if n.failure_reason]
        most_common_reason = max(set(reasons), key=reasons.count) if reasons else None

        return {
            "total_tasks": total,
            "failed_tasks": len(failed),
            "failure_rate": round(failure_rate, 3),
            "worst_agent": worst_agent,
            "worst_agent_failures": self._agent_failure_counts.get(worst_agent, 0) if worst_agent else 0,
            "most_common_reason": most_common_reason,
            "agent_failure_counts": dict(self._agent_failure_counts),
        }

    def get_recent_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Son N başarısız görevi döner (en yeni önce)."""
        failed = sorted(
            [n for n in self._nodes.values() if n.status == "failed"],
            key=lambda n: n.completed_at or datetime.min,
            reverse=True
        )
        return [
            {
                "task_id": n.task_id,
                "title": n.title,
                "agent_id": n.agent_id,
                "failure_reason": n.failure_reason,
                "causal_root": n.causal_root,
                "attempts": n.attempt_count,
                "duration_s": n.duration_s,
            }
            for n in failed[:limit]
        ]

    def get_summary(self) -> Dict[str, Any]:
        """AGI ContextPackage entegrasyonu için özet."""
        patterns = self.get_failure_patterns()
        patterns["recent_failures"] = self.get_recent_failures(5)
        return patterns

    async def sync_from_db(self, db) -> None:
        """
        DB'deki son görev kayıtlarını yükler (startup hydration).
        """
        try:
            from packages.persistence.repository import ProjectRepository, SubTaskRepository
            recent = await ProjectRepository.list_recent(db, limit=100)
            for p in recent:
                task_id = str(p.id)
                if task_id not in self._nodes:
                    node = self.register_task(task_id, p.title or "Unnamed", p.assigned_agent or "system")
                    node.status = p.status
                    node.started_at = p.started_at
                    node.completed_at = p.completed_at
                    if p.status == "error":
                        node.status = "failed"
                        node.failure_reason = p.error_detail
            _log.info(f"[TASK-GRAPH] {len(recent)} görev DB'den senkronize edildi.")
        except Exception as e:
            _log.warning(f"[TASK-GRAPH] DB sync hatası: {e}")


# Singleton
task_state_graph = TaskStateGraph()
