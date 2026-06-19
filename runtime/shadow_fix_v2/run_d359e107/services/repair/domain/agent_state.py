"""
Ajan Durum Makinesi
Her ajanın yaşam döngüsünü yönetir:

    HEALTHY ──-> DEGRADED ──-> ISOLATED ──-> RECOVERING ──-> HEALTHY
                    │                          │
                    └──────────── DEAD ────────┘

Geçişler yalnızca bu modül üzerinden olur — dışarıdan doğrudan skor değiştirilmez.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class AgentState(str, Enum):
    HEALTHY    = "healthy"     # Normal çalışma
    DEGRADED   = "degraded"    # Uyarı bölgesi
    ISOLATED   = "isolated"    # Yük almıyor, kurtarma bekleniyor
    RECOVERING = "recovering"  # Kurtarma deneniyor
    DEAD       = "dead"        # Tüm kurtarma girişimleri başarısız


# Geçerli durum geçişleri (FSM)
TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.HEALTHY:    {AgentState.DEGRADED},
    AgentState.DEGRADED:   {AgentState.HEALTHY, AgentState.ISOLATED},
    AgentState.ISOLATED:   {AgentState.RECOVERING, AgentState.DEAD},
    AgentState.RECOVERING: {AgentState.HEALTHY, AgentState.ISOLATED, AgentState.DEAD},
    AgentState.DEAD:       {AgentState.RECOVERING},  # Manuel reset ile
}

SCORE_THRESHOLDS = {
    "healthy":   0.70,
    "degraded":  0.40,
    "critical":  0.20,
}


@dataclass
class AgentSnapshot:
    agent_id:       str
    state:          AgentState = AgentState.HEALTHY
    score:          float      = 1.0
    score_history:  list[float] = field(default_factory=list)  # Son 10 ölçüm
    fail_streak:    int         = 0
    recovery_attempts: int      = 0
    last_transition: float      = field(default_factory=time.time)
    last_success:    float      = field(default_factory=time.time)
    quarantine_until: float     = 0.0    # Bu zamana kadar yük alma
    error_types:    dict[str, int] = field(default_factory=dict)  # hata_tipi -> sayı
    latency_history: list[float] = field(default_factory=list)  # Son 10 işlem süresi

    MAX_HISTORY = 10
    MAX_RECOVERY_ATTEMPTS = 4

    def update_score(self, new_score: float):
        self.score = new_score
        self.score_history.append(new_score)
        if len(self.score_history) > self.MAX_HISTORY:
            self.score_history.pop(0)

    @property
    def avg_latency(self) -> float:
        if not self.latency_history:
            return 0.0
        return sum(self.latency_history) / len(self.latency_history)

    def record_latency(self, seconds: float):
        self.latency_history.append(seconds)
        if len(self.latency_history) > self.MAX_HISTORY:
            self.latency_history.pop(0)

    @property
    def trend(self) -> float:
        """Pozitif = iyileşiyor, negatif = kötüleşiyor."""
        h = self.score_history
        if len(h) < 3:
            return 0.0
        mid = len(h) // 2
        return sum(h[mid:]) / len(h[mid:]) - sum(h[:mid]) / len(h[:mid])

    @property
    def avg_score(self) -> float:
        if not self.score_history:
            return self.score
        return sum(self.score_history) / len(self.score_history)

    def record_error(self, error_type: str):
        self.fail_streak += 1
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1

    def record_success(self):
        self.fail_streak = 0
        self.last_success = time.time()

    def can_transition(self, target: AgentState) -> bool:
        return target in TRANSITIONS.get(self.state, set())

    def transition(self, target: AgentState, reason: str = "") -> bool:
        if not self.can_transition(target):
            return False
        self.state = target
        self.last_transition = time.time()
        return True

    def is_quarantined(self) -> bool:
        return time.time() < self.quarantine_until

    def quarantine(self, seconds: float):
        self.quarantine_until = time.time() + seconds

    @property
    def dominant_error(self) -> str:
        if not self.error_types:
            return "unknown"
        return max(self.error_types, key=self.error_types.get)

    def to_dict(self) -> dict:
        return {
            "agent_id":          self.agent_id,
            "state":             self.state,
            "score":             round(self.score, 3),
            "avg_score":         round(self.avg_score, 3),
            "trend":             round(self.trend, 3),
            "fail_streak":       self.fail_streak,
            "recovery_attempts": self.recovery_attempts,
            "dominant_error":    self.dominant_error,
            "quarantined_secs":  max(0, round(self.quarantine_until - time.time(), 1)),
            "state_age_secs":    round(time.time() - self.last_transition, 1),
        }
