"""
WorldModel Katman 9.4: Causal Error Graph
[FIX-9] Sistem genelinde tekrarlayan hata örüntülerini nedensel bağlantılarıyla
depolar. CausalEngine'den beslenen bu grafik, AGI'nin "şu ajan şu koşulda bu
hatayı üretiyor" ilişkisini sistematik olarak öğrenmesini sağlar.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from packages.observability.logging import get_logger

_log = get_logger("world_causal_error_graph")


@dataclass
class ErrorPattern:
    """Belirli bir hata örüntüsünün kaydı."""
    pattern_id: str
    error_type: str                  # ör: "rate_limit_429", "llm_timeout", "assertion_failed"
    agent_id: str
    root_cause: str                  # CausalEngine'den gelen kök neden özeti
    occurrence_count: int = 1
    confidence: float = 0.8
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    related_task_ids: List[str] = field(default_factory=list)
    preventive_action: Optional[str] = None  # Önerilen önlem
    metadata: Dict[str, Any] = field(default_factory=dict)

    def increment(self, task_id: str = ""):
        self.occurrence_count += 1
        self.last_seen = datetime.now(timezone.utc)
        if task_id and task_id not in self.related_task_ids:
            self.related_task_ids.append(task_id)
        # Tekrarladıkça güven artar
        self.confidence = min(0.99, self.confidence + 0.02)


class CausalErrorGraph:
    """
    WorldModel Katman 9.4: Nedensel Hata Grafiği.
    
    Sistematik olarak:
    - CausalEngine'den gelen hata-neden bağlantılarını kaydeder
    - Aynı pattern'in tekrarını takip eder
    - Her hata için önerilen önleyici eylemi (preventive_action) saklar
    - AGI'ye "daha önce bu senaryoda ne oldu?" sorusunu yanıtlar
    """

    def __init__(self):
        self._patterns: Dict[str, ErrorPattern] = {}

    def _make_pattern_id(self, error_type: str, agent_id: str, root_cause: str) -> str:
        """Aynı hata örüntüsü için deterministik ID üretir."""
        raw = f"{error_type}::{agent_id}::{root_cause[:50]}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def record_error(
        self,
        error_type: str,
        agent_id: str,
        root_cause: str,
        task_id: str = "",
        confidence: float = 0.8,
        preventive_action: str = "",
        metadata: Dict[str, Any] = None
    ) -> ErrorPattern:
        """
        Yeni bir hata örüntüsü kaydeder veya mevcut örüntüyü günceller.
        """
        pid = self._make_pattern_id(error_type, agent_id, root_cause)

        if pid in self._patterns:
            pattern = self._patterns[pid]
            pattern.increment(task_id)
            if preventive_action:
                pattern.preventive_action = preventive_action
            _log.debug(f"[ERROR-GRAPH] Tekrarlayan hata: {error_type}/{agent_id} (#{pattern.occurrence_count})")
        else:
            pattern = ErrorPattern(
                pattern_id=pid,
                error_type=error_type,
                agent_id=agent_id,
                root_cause=root_cause,
                confidence=confidence,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                related_task_ids=[task_id] if task_id else [],
                preventive_action=preventive_action,
                metadata=metadata or {}
            )
            self._patterns[pid] = pattern
            _log.info(f"[ERROR-GRAPH] Yeni hata örüntüsü: {error_type} | Agent: {agent_id} | Neden: {root_cause[:60]}")

        return pattern

    def ingest_causal_graph(self, causal_graph, episode_id: str = "", agent_id: str = "system"):
        """
        CausalEngine'den dönen CausalGraph'ı alır ve içindeki
        'causes_failure' bağlarını ErrorPattern olarak kaydeder.
        """
        if causal_graph is None:
            return
        for link in (causal_graph.links or []):
            if link.relationship_type == "causes_failure":
                self.record_error(
                    error_type=link.effect_id or "unknown_failure",
                    agent_id=agent_id,
                    root_cause=link.cause_id or "unknown_cause",
                    task_id=episode_id,
                    confidence=link.confidence,
                    metadata=link.metadata or {}
                )

    def get_patterns_for_agent(self, agent_id: str) -> List[ErrorPattern]:
        """Belirli bir ajan için bilinen hata örüntülerini döner."""
        return [p for p in self._patterns.values() if p.agent_id == agent_id]

    def get_high_confidence_patterns(self, min_confidence: float = 0.85,
                                     min_occurrences: int = 2) -> List[ErrorPattern]:
        """
        Yüksek güvenirlikte ve sık tekrarlayan örüntüleri döner.
        AGI, bunları ContextPackage'e 'failure_patterns' olarak ekler.
        """
        return sorted(
            [
                p for p in self._patterns.values()
                if p.confidence >= min_confidence and p.occurrence_count >= min_occurrences
            ],
            key=lambda p: p.occurrence_count,
            reverse=True
        )

    def get_context_hints(self, agent_id: str = None) -> List[str]:
        """
        AGI'ye aktarılacak hata uyarı listesi.
        ContextPackage.failure_patterns alanına doğrudan beslenir.
        """
        patterns = self.get_high_confidence_patterns()
        if agent_id:
            patterns = [p for p in patterns if p.agent_id == agent_id]

        hints = []
        for p in patterns[:10]:
            hint = (
                f"[FAILURE-PATTERN] Ajan '{p.agent_id}' sıklıkla '{p.error_type}' üretiyor. "
                f"Kök Neden: {p.root_cause}. "
                f"Tekrar: {p.occurrence_count}x. "
            )
            if p.preventive_action:
                hint += f"Öneri: {p.preventive_action}"
            hints.append(hint)
        return hints

    def get_summary(self) -> Dict[str, Any]:
        """AGI ContextPackage entegrasyonu için özet."""
        total = len(self._patterns)
        critical = [p for p in self._patterns.values() if p.occurrence_count >= 5]
        return {
            "total_patterns": total,
            "critical_patterns": len(critical),
            "context_hints": self.get_context_hints(),
            "top_failing_agents": sorted(
                {p.agent_id: sum(
                    1 for pp in self._patterns.values() if pp.agent_id == p.agent_id
                ) for p in self._patterns.values()}.items(),
                key=lambda x: x[1], reverse=True
            )[:5],
        }


# Singleton
causal_error_graph = CausalErrorGraph()
