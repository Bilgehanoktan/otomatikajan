"""
Kök Neden Analizörü
• Hata mesajından tip tespiti (regex + anahtar kelime)
• Tekrarlayan hata kümeleme
• Sistem geneli anomali tespiti
• Trend analizi (kötüleşiyor mu, iyileşiyor mu?)
"""

import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packages.healing.domain.agent_state import AgentSnapshot


# ── Hata Sınıflandırma ────────────────────────────────────
ERROR_PATTERNS: list[tuple[str, list[str]]] = [
    ("RateLimitError",     ["rate limit", "429", "too many requests", "quota exceeded"]),
    ("ContextLengthError", ["context length", "maximum tokens", "token limit", "context window"]),
    ("TimeoutError",       ["timeout", "timed out", "deadline exceeded", "read timeout"]),
    ("AuthError",          ["401", "403", "unauthorized", "invalid api key", "authentication"]),
    ("NetworkError",       ["connection", "network", "dns", "ssl", "socket", "unreachable"]),
    ("ServerError",        ["500", "502", "503", "504", "server error", "internal error"]),
    ("ParseError",         ["json", "parse", "decode", "invalid response", "unexpected"]),
    ("InternalError",      ["attributeerror", "nameerror", "typeerror", "uuid", "keyerror", "recursion"]),
    ("DatabaseError",      ["sqlalchemy", "psycopg", "sqlite", "operationalerror", "integrityerror", "connection refused"]),
    ("MemoryPressure",     ["memory", "allocation", "oom", "resource exhausted"]),
]


def classify_error(error_msg: str) -> str:
    msg_lower = error_msg.lower()
    for error_type, keywords in ERROR_PATTERNS:
        if any(kw in msg_lower for kw in keywords):
            return error_type
    return "unknown"


# ── Anomali Tespiti ───────────────────────────────────────
@dataclass
class AnomalyReport:
    agent_id:    str
    anomaly:     str
    severity:    str      # "warning" | "critical"
    evidence:    str
    detected_at: float = field(default_factory=time.time)


class RootCauseAnalyzer:
    """
    Tüm ajanların hata geçmişini izler.
    Sistem genelinde örüntüler ve anomaliler tespit eder.
    """

    def __init__(self):
        # agent_id -> [(timestamp, error_type), ...]
        self._error_timeline: dict[str, list[tuple[float, str]]] = defaultdict(list)
        self._anomalies: list[AnomalyReport] = []
        self._last_analysis: float = 0.0
        self.ANALYSIS_WINDOW = 300  # 5 dakika

    def record(self, agent_id: str, error_msg: str) -> str:
        """Hatayı kaydet, tipini döndür."""
        error_type = classify_error(error_msg)
        self._error_timeline[agent_id].append((time.time(), error_type))
        self._prune_old(agent_id)
        return error_type

    def analyze(self, snapshots: "dict[str, AgentSnapshot]") -> list[AnomalyReport]:
        """
        Tüm snapshots'ları analiz et, anomali listesi döndür.
        Her 30 saniyede bir çalışır.
        """
        if time.time() - self._last_analysis < 30:
            return self._anomalies[-10:]

        self._last_analysis = time.time()
        new_anomalies = []

        for agent_id, snap in snapshots.items():
            new_anomalies.extend(self._check_error_burst(agent_id, snap))
            new_anomalies.extend(self._check_trend(agent_id, snap))

        new_anomalies.extend(self._check_cascade(snapshots))

        self._anomalies.extend(new_anomalies)
        # Son 100 anomali tut
        self._anomalies = self._anomalies[-100:]
        return new_anomalies

    def _check_error_burst(self, agent_id: str, snap: "AgentSnapshot") -> list[AnomalyReport]:
        """Son 2 dakikada 5+ hata -> patlama tespiti."""
        timeline = self._error_timeline.get(agent_id, [])
        cutoff = time.time() - 120
        recent = [et for ts, et in timeline if ts > cutoff]
        if len(recent) >= 5:
            dominant = Counter(recent).most_common(1)[0]
            return [AnomalyReport(
                agent_id=agent_id,
                anomaly="error_burst",
                severity="critical",
                evidence=f"2 dk içinde {len(recent)} hata, baskın tip: {dominant[0]} ({dominant[1]}x)",
            )]
        return []

    def _check_trend(self, agent_id: str, snap: "AgentSnapshot") -> list[AnomalyReport]:
        """Sürekli düşüş trendi -> erken uyarı."""
        if snap.trend < -0.15 and len(snap.score_history) >= 5:
            return [AnomalyReport(
                agent_id=agent_id,
                anomaly="score_decline",
                severity="warning",
                evidence=f"Trend: {snap.trend:+.3f}, ort skor: {snap.avg_score:.2f}",
            )]
        return []

    def _check_cascade(self, snapshots: "dict[str, AgentSnapshot]") -> list[AnomalyReport]:
        """Birden fazla ajan aynı anda çökerse -> cascade failure."""
        critical = [
            aid for aid, snap in snapshots.items()
            if snap.score < 0.3
        ]
        if len(critical) >= 3:
            return [AnomalyReport(
                agent_id="system",
                anomaly="cascade_failure",
                severity="critical",
                evidence=f"{len(critical)} ajan kritik: {critical}",
            )]
        return []

    def _prune_old(self, agent_id: str):
        """ANALYSIS_WINDOW dışındaki kayıtları sil."""
        cutoff = time.time() - self.ANALYSIS_WINDOW
        self._error_timeline[agent_id] = [
            (ts, et) for ts, et in self._error_timeline[agent_id]
            if ts > cutoff
        ]

    def error_summary(self, agent_id: str) -> dict:
        """Bir ajanın hata dağılım özeti."""
        timeline = self._error_timeline.get(agent_id, [])
        if not timeline:
            return {}
        types = Counter(et for _, et in timeline)
        return dict(types.most_common())

    def system_summary(self) -> dict:
        """Sistem geneli hata özeti."""
        all_errors = [et for tl in self._error_timeline.values() for _, et in tl]
        return {
            "total_errors":   len(all_errors),
            "by_type":        dict(Counter(all_errors).most_common()),
            "recent_anomalies": [
                {"agent": a.agent_id, "type": a.anomaly, "severity": a.severity, "evidence": a.evidence}
                for a in self._anomalies[-5:]
            ],
        }
