"""
Metrik Toplayıcı — Faz 2
• In-memory sayaçlar (Prometheus entegrasyonu için hazır)
• LLM çağrı latency histogramı
• Ajan başarı/hata sayaçları
• /metrics endpoint'i için veri sağlar
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Deque


@dataclass
class LatencyBucket:
    """Son N ölçümün istatistiği."""
    _data: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))

    def record(self, seconds: float):
        self._data.append(seconds)

    @property
    def p50(self) -> float:
        if not self._data: return 0.0
        s = sorted(self._data)
        return s[len(s) // 2]

    @property
    def p95(self) -> float:
        if not self._data: return 0.0
        s = sorted(self._data)
        return s[int(len(s) * 0.95)]

    @property
    def p99(self) -> float:
        if not self._data: return 0.0
        s = sorted(self._data)
        return s[int(len(s) * 0.99)]

    @property
    def avg(self) -> float:
        return sum(self._data) / len(self._data) if self._data else 0.0

    @property
    def count(self) -> int:
        return len(self._data)

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "avg_s":  round(self.avg, 3),
            "p50_s":  round(self.p50, 3),
            "p95_s":  round(self.p95, 3),
            "p99_s":  round(self.p99, 3),
        }


class MetricsCollector:
    """Thread-safe metrik toplayıcı."""

    def __init__(self):
        self._lock = Lock()
        self._started_at = time.time()

        # Sayaçlar
        self._counters: dict[str, int] = defaultdict(int)

        # Latency
        self._latencies: dict[str, LatencyBucket] = defaultdict(LatencyBucket)

        # Hata tiplerini say
        self._errors: dict[str, int] = defaultdict(int)

    # ── Kayıt metodları ───────────────────────────────────
    def inc(self, name: str, value: int = 1):
        with self._lock:
            self._counters[name] += value

    def record_latency(self, name: str, seconds: float):
        self._latencies[name].record(seconds)

    def record_error(self, error_type: str):
        with self._lock:
            self._errors[error_type] += 1

    def record_llm_call(
        self,
        provider: str,
        latency_s: float,
        success: bool,
        tokens: int = 0,
        cost_usd: float = 0.0,
    ):
        self.record_latency(f"llm.{provider}.latency", latency_s)
        self.inc(f"llm.{provider}.calls.total")
        self.inc(f"llm.{provider}.tokens", tokens)
        if success:
            self.inc(f"llm.{provider}.calls.success")
        else:
            self.inc(f"llm.{provider}.calls.failure")
        self.inc("llm.cost.microdollars", int(cost_usd * 1_000_000))

    def record_project(self, success: bool, duration_s: float):
        self.inc("projects.total")
        self.record_latency("projects.duration", duration_s)
        if success:
            self.inc("projects.success")
        else:
            self.inc("projects.failure")

    def record_heal_action(self, strategy: str, success: bool):
        self.inc("heal.actions.total")
        self.inc(f"heal.strategy.{strategy}")
        if success:
            self.inc("heal.actions.success")
        else:
            self.inc("heal.actions.failure")

    # ── Snapshot ─────────────────────────────────────────
    def snapshot(self) -> dict:
        with self._lock:
            counters = dict(self._counters)
            errors   = dict(self._errors)

        latencies = {
            name: bucket.to_dict()
            for name, bucket in self._latencies.items()
        }

        uptime_s = time.time() - self._started_at

        return {
            "uptime_s":  round(uptime_s, 1),
            "uptime_hms": _fmt_uptime(uptime_s),
            "counters":  counters,
            "latencies": latencies,
            "errors":    errors,
            "computed":  self._computed(counters),
        }

    def _computed(self, c: dict) -> dict:
        providers = ("openai", "anthropic", "gemini", "openrouter", "groq", "nvidia")
        total_llm    = sum(c.get(f"llm.{p}.calls.total", 0) for p in providers)
        success_llm  = sum(c.get(f"llm.{p}.calls.success", 0) for p in providers)
        total_proj   = c.get("projects.total", 0)
        success_proj = c.get("projects.success", 0)
        total_cost   = c.get("llm.cost.microdollars", 0) / 1_000_000

        from services.repair.application.heal_engine import heal_engine
        return {
            "llm_success_rate_pct": round(success_llm / total_llm * 100, 1) if total_llm else 0.0,
            "project_success_rate_pct": round(success_proj / total_proj * 100, 1) if total_proj else 0.0,
            "total_llm_calls":   total_llm,
            "total_projects":    total_proj,
            "total_cost_usd":    round(total_cost, 6),
            "heal_success_rate_pct": self._heal_rate(c),
            "system_score":      heal_engine.system_health_score() if hasattr(heal_engine, "system_health_score") else 1.0,
        }

    def _heal_rate(self, c: dict) -> float:
        total   = c.get("heal.actions.total", 0)
        success = c.get("heal.actions.success", 0)
        return round(success / total * 100, 1) if total else 0.0


def _fmt_uptime(s: float) -> str:
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


# ── Singleton ─────────────────────────────────────────────
metrics = MetricsCollector()
