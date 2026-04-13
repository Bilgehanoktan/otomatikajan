"""
╔══════════════════════════════════════════════════════════════════╗
║              ÖZ-İYİLEŞTİRME MOTORU v2 — Tam Sürüm              ║
╠══════════════════════════════════════════════════════════════════╣
║  Döngü:  İZLE -> ANALİZ ET -> KARAR VER -> MÜDAHALE ET -> DOĞRULA  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from enum import Enum

from heal.agent_state import AgentSnapshot, AgentState, SCORE_THRESHOLDS
from heal.recovery_strategies import get_strategy_chain, RecoveryResult
from heal.root_cause import RootCauseAnalyzer


class Severity(str, Enum):
    """Test uyumluluğu ve event bus için severity sabitleri."""
    INFO     = "info"
    WARNING  = "warning"
    CRITICAL = "critical"
    RESOLVED = "resolved"
    ACTION   = "action"

if TYPE_CHECKING:
    from core.orchestrator import Orchestrator, SubTask


@dataclass
class HealEvent:
    timestamp:  str
    agent_id:   str
    severity:   str
    phase:      str
    message:    str
    strategy:   str   = ""
    success:    bool  = True
    duration_s: float = 0.0


SEVERITY_ICONS = {
    "info": "[INFO]", "warning": "[WARN]",
    "critical": "[CRIT]", "resolved": "[DONE]", "action": "[ACT]",
}


class SelfHealEngine:
    CHECK_INTERVAL     = 5.0
    VERIFY_DELAY       = 8.0
    WARN_THRESHOLD     = SCORE_THRESHOLDS["healthy"]
    CRITICAL_THRESHOLD = SCORE_THRESHOLDS["degraded"]
    DEAD_THRESHOLD     = SCORE_THRESHOLDS["critical"]

    def __init__(self, orchestrator: "Orchestrator"):
        self.orch     = orchestrator
        self.rca      = RootCauseAnalyzer()
        self._snaps:  dict[str, AgentSnapshot] = {}
        self._events: list[HealEvent]          = []
        self._active_recoveries: set[str]      = set()
        self._recovery_history: dict[str, list[RecoveryResult]] = {}

        # ── Test uyumluluğu için public alias'lar ─────────
        # engine.log      -> _events listesi (HealEvent nesneleri)
        # engine.suppressed -> throttle set'i (birden fazla tetiklenmeyi engeller)
        # engine._backup_mode -> backup modunda olan agent'lar
        self.suppressed:   set[str]  = set()   # throttle: aynı ajan tekrar tetiklenmesin
        self._backup_mode: set[str]  = set()   # backup/isolated ajanlar

    # ── Ana Döngü ─────────────────────────────────────────
    async def monitor_loop(self):
        from config import ENABLE_HEALING
        if not ENABLE_HEALING:
            self._log("system", "info", "monitor", "Öz-İyileştirme Motoru yapılandırma gereği DEVRE DIŞI.")
            return

        self._log("system", "info", "monitor", "Oz-Iyileshirme Motoru v2 bashladi.")
        while True:
            try:
                await asyncio.sleep(self.CHECK_INTERVAL)
                await self._cycle()
            except asyncio.CancelledError:
                self._log("system", "info", "monitor", "Motor durduruldu.")
                break
            except Exception as e:
                self._log("system", "warning", "monitor", f"Döngü iç hata: {e}")

    async def _cycle(self):
        raw_health = self.orch.get_health()
        self._sync_snapshots(raw_health)
        anomalies = self.rca.analyze(self._snaps)
        for anomaly in anomalies:
            self._log(anomaly.agent_id, anomaly.severity, "analyze",
                      f"Anomali: {anomaly.anomaly} — {anomaly.evidence}")
        for agent_id, snap in self._snaps.items():
            if agent_id not in self._active_recoveries:
                await self._decide_and_act(snap)

    # ── FSM Geçişleri ─────────────────────────────────────
    def _sync_snapshots(self, raw_health: dict):
        for agent_id, score in raw_health.items():
            if agent_id not in self._snaps:
                self._snaps[agent_id] = AgentSnapshot(agent_id=agent_id)
            snap = self._snaps[agent_id]
            snap.update_score(score)
            self._fsm_transition(snap, score)

    def _fsm_transition(self, snap: AgentSnapshot, score: float):
        current = snap.state
        target  = self._score_to_target(snap, score)
        if target != current and snap.transition(target):
            self._log(snap.agent_id, self._state_severity(target), "monitor",
                      f"Durum: {current} -> {target} (skor={score:.2f})")

    def _score_to_target(self, snap: AgentSnapshot, score: float) -> AgentState:
        # Legacy uyumluluk: çok düşük skor ilk kontrolde DEGRADED, bir sonraki kontrolde ISOLATED olur.
        if score >= self.WARN_THRESHOLD:
            return AgentState.HEALTHY
        if snap.state == AgentState.HEALTHY:
            return AgentState.DEGRADED
        if score >= self.CRITICAL_THRESHOLD:
            return AgentState.DEGRADED
        if snap.recovery_attempts >= AgentSnapshot.MAX_RECOVERY_ATTEMPTS:
            return AgentState.DEAD
        return AgentState.ISOLATED

    def _state_severity(self, state: AgentState) -> str:
        return {
            AgentState.HEALTHY: "resolved", AgentState.DEGRADED: "warning",
            AgentState.ISOLATED: "critical", AgentState.RECOVERING: "action",
            AgentState.DEAD: "critical",
        }.get(state, "info")

    # ── Karar & Müdahale ──────────────────────────────────
    async def _decide_and_act(self, snap: AgentSnapshot):
        if snap.state == AgentState.HEALTHY:
            if snap.recovery_attempts > 0:
                snap.recovery_attempts = 0
                self._log(snap.agent_id, "resolved", "decide", "İyileşti, sayaç sıfırlandı.")
        elif snap.state == AgentState.DEGRADED:
            self._log(snap.agent_id, "warning", "decide",
                      f"Degraded: ort={snap.avg_score:.2f}, trend={snap.trend:+.2f}")
        elif snap.state == AgentState.DEAD:
            self._log(snap.agent_id, "critical", "decide",
                      f"DEAD — {snap.recovery_attempts} başarısız girişim.")
        elif snap.state in (AgentState.ISOLATED, AgentState.RECOVERING):
            if snap.is_quarantined():
                secs = snap.quarantine_until - time.time()
                self._log(snap.agent_id, "info", "decide", f"Karantina: {secs:.0f}sn kaldı.")
            else:
                asyncio.create_task(self._recover(snap))

    # ── Kurtarma ──────────────────────────────────────────
    async def _recover(self, snap: AgentSnapshot):
        if snap.agent_id in self._active_recoveries:
            return
        self._active_recoveries.add(snap.agent_id)
        snap.state = AgentState.RECOVERING
        snap.recovery_attempts += 1
        self._log(snap.agent_id, "action", "act",
                  f"Kurtarma #{snap.recovery_attempts} — hata: {snap.dominant_error}")

        chain = get_strategy_chain(snap.dominant_error)
        final: RecoveryResult | None = None

        for strategy in chain:
            self._log(snap.agent_id, "action", "act", f"Strateji: {strategy.name}")
            try:
                dummy = _DummySubTask(snap.agent_id)
                result = await asyncio.wait_for(
                    strategy.execute(snap, dummy, self.orch), timeout=25.0)
                final = result
                if snap.agent_id not in self._recovery_history:
                    self._recovery_history[snap.agent_id] = []
                self._recovery_history[snap.agent_id].append(result)
                if result.success:
                    self._log(snap.agent_id, "action", "act",
                              f"✓ {strategy.name} ({result.duration_s:.1f}sn): {result.message}")
                    break
                else:
                    self._log(snap.agent_id, "warning", "act",
                              f"✗ {strategy.name}: {result.message}")
            except asyncio.TimeoutError:
                self._log(snap.agent_id, "warning", "act", f"✗ {strategy.name}: zaman aşımı")
            except Exception as e:
                self._log(snap.agent_id, "warning", "act", f"✗ {strategy.name}: {e}")

        await asyncio.sleep(self.VERIFY_DELAY)
        await self._verify(snap)
        self._active_recoveries.discard(snap.agent_id)

    async def _verify(self, snap: AgentSnapshot):
        new_score = self.orch.get_health().get(snap.agent_id, snap.score)
        snap.update_score(new_score)
        if new_score >= self.WARN_THRESHOLD:
            snap.transition(AgentState.HEALTHY)
            self._log(snap.agent_id, "resolved", "verify",
                      f"Kurtarma doğrulandı — skor={new_score:.2f}")
        elif new_score >= self.CRITICAL_THRESHOLD:
            snap.transition(AgentState.DEGRADED)
            self._log(snap.agent_id, "warning", "verify",
                      f"Kısmi iyileşme — skor={new_score:.2f}")
        else:
            if snap.recovery_attempts >= AgentSnapshot.MAX_RECOVERY_ATTEMPTS:
                snap.transition(AgentState.DEAD)
                self._log(snap.agent_id, "critical", "verify",
                          f"Tüm girişimler tükendi ({snap.recovery_attempts}). DEAD.")
            else:
                snap.transition(AgentState.ISOLATED)
                snap.quarantine(60)
                self._log(snap.agent_id, "warning", "verify",
                          f"Başarısız, 60sn karantina.")

    # ── Orchestrator Entegrasyonu ─────────────────────────
    async def on_subtask_error(self, agent_id: str, error_msg: str):
        snap = self._snaps.get(agent_id)
        if not snap:
            return
        error_type = self.rca.record(agent_id, error_msg)
        snap.record_error(error_type)
        self._log(agent_id, "warning", "monitor",
                  f"Hata: {error_type} (streak={snap.fail_streak})")
        
        # Faz 12 Hardening: Otomatik Karantina (Quarantine) logic
        # Eğer kritik bir hata ise veya hata serisi uzadıysa ajanı karantinaya al
        if snap.fail_streak >= 2 or error_type in ("TimeoutError", "RateLimitError", "AuthError"):
            q_time = 60 * snap.fail_streak # Streak arttıkça süre uzar
            snap.quarantine(q_time)
            self._log(agent_id, "critical", "monitor", f"Otomatik Karantina: {error_type} nedeniyle {q_time}sn devre dışı.")

    def on_subtask_success(self, agent_id: str, duration_s: float = 0.0):
        snap = self._snaps.get(agent_id)
        if snap:
            snap.record_success()
            if duration_s > 0:
                snap.record_latency(duration_s)
                
                # Latency-based Quarantine: Son 3 işlemin ortalaması 25sn üzerindeyse
                avg_lat = getattr(snap, "avg_latency", 0.0)
                if len(snap.latency_history) >= 3 and isinstance(avg_lat, (int, float)) and avg_lat > 25.0:
                    snap.quarantine(120) # 2 dakika dinlendir
                    self._log(agent_id, "warning", "monitor", 
                              f"Latency Karantinası: Ortalama {float(avg_lat):.1f}sn gecikme nedeniyle 120sn kısıtlandı.")

    async def recover_subtask(self, agent_id: str, subtask: "SubTask") -> bool:
        snap = self._snaps.get(agent_id)
        if not snap:
            return False
        chain = get_strategy_chain(snap.dominant_error)
        for strategy in chain:
            try:
                result = await asyncio.wait_for(
                    strategy.execute(snap, subtask, self.orch), timeout=20.0)
                if result.success:
                    self._log(agent_id, "action", "act",
                              f"Subtask kurtarıldı: {strategy.name}")
                    return True
            except Exception:
                continue
        return False

    # ── Log & API ─────────────────────────────────────────
    @property
    def log(self) -> list[HealEvent]:
        """Test uyumluluğu: engine.log -> _events listesi."""
        return self._events

    def _log(self, agent_id, severity, phase, message, strategy="", success=True, duration_s=0.0):
        e = HealEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id, severity=severity, phase=phase,
            message=message, strategy=strategy, success=success, duration_s=duration_s,
        )
        self._events.append(e)
        icon = SEVERITY_ICONS.get(severity, "  ")
        _log = __import__("observability.logging", fromlist=["get_logger"]).get_logger("heal_engine")
        _log.info(f"{icon} [{e.timestamp[11:19]}][{phase:7}][{agent_id:12}] {message}")
        
        # Faz 12 Hardening: Vektör Belleğe (Watchdog) aktar
        try:
            from memory.watchdog import watchdog
            import asyncio
            coro = watchdog.log_event(agent_id, severity, phase, message)
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.ensure_future(coro)
        except Exception:
            pass
        
        # Domain event bus'a yayınla (bağlantı varsa)
        try:
            import asyncio
            from core.events import event_bus
            coro = event_bus.emit(
                f"heal.{severity}",
                agent_id=agent_id, severity=severity, phase=phase,
                message=message, strategy=strategy,
            )
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.ensure_future(coro)
        except Exception:
            pass

    def system_health_score(self) -> float:
        """Faz 12 Hardening: Ağırlıklı, Latency ve Resource Aware Sağlık Skoru."""
        h = self.orch.get_health()
        if not h:
            return 1.0

        # 1. Ağırlıklı Ajan Skoru
        CRITICAL_AGENTS = {"orchestrator": 2.5, "database": 2.0, "llm_client": 1.5}
        total_weight = 0.0
        weighted_score_sum = 0.0

        for agent_id, score in h.items():
            weight = CRITICAL_AGENTS.get(agent_id, 1.0)
            total_weight += weight
            weighted_score_sum += (score * weight)

        base_score = weighted_score_sum / total_weight if total_weight > 0 else 1.0

        # 2. Latency Penalty: Ortalama gecikme 20sn üzerindeyse skor düşer
        latency_penalty = 0.0
        valid_latencies = [s.avg_latency for s in self._snaps.values() if hasattr(s, "avg_latency") and s.avg_latency > 0]
        if valid_latencies:
            avg_system_latency = sum(valid_latencies) / len(valid_latencies)
            if avg_system_latency > 20.0:
                # 20sn'den sonra her 10sn için -0.1 ceza
                latency_penalty = min(0.4, (avg_system_latency - 20.0) / 100.0)

        # 3. Bellek (RAM) Multiplier
        mem_multiplier = 1.0
        try:
            import psutil
            import os
            # Use safe memory inspection
            p = psutil.Process(os.getpid())
            mem_mb = p.memory_info().rss / 1024 / 1024
            if mem_mb > 750: # 750MB üstünde baskı başlar
                mem_multiplier = max(0.4, 1.0 - ((mem_mb - 750) / 1500))
        except Exception:
            pass

        final_score = (base_score - latency_penalty) * mem_multiplier
        return round(float(max(0.0, min(1.0, final_score))), 3)

    def recent_events(self, n: int = 30) -> list[dict]:
        return [
            {"timestamp": e.timestamp, "agent_id": e.agent_id, "severity": e.severity,
             "phase": e.phase, "message": e.message, "strategy": e.strategy}
            for e in self._events[-n:]
        ]

    def agent_snapshots(self) -> list[dict]:
        return [s.to_dict() for s in self._snaps.values()]

    def recovery_history(self, agent_id: str) -> list[dict]:
        return [
            {"strategy": r.strategy, "success": r.success,
             "message": r.message, "duration_s": round(float(r.duration_s or 0), 2)}
            for r in self._recovery_history.get(agent_id, [])
        ]

    def system_report(self) -> dict:
        states = {s.value: 0 for s in AgentState}
        for snap in self._snaps.values():
            states[snap.state.value] += 1
        return {
            "system_score":      self.system_health_score(),
            "agent_states":      states,
            "active_recoveries": list(self._active_recoveries),
            "rca_summary":       self.rca.system_summary(),
            "total_events":      len(self._events),
            "snapshots":         self.agent_snapshots(),
        }

    def agents_in_backup(self) -> list[str]:
        """_backup_mode set'i + snap state'den birleşik liste."""
        from_state = {aid for aid, snap in self._snaps.items()
                     if snap.state in (AgentState.ISOLATED, AgentState.RECOVERING)}
        return list(self._backup_mode | from_state)

    async def _check_all(self):
        """Test compat alias: _cycle ile aynı ama suppressed throttle'ı uygular.
        suppressed.clear() yapılınca bir sonraki çağrıda tekrar tetiklenir.
        """
        raw_health = self.orch.get_health()
        self._sync_snapshots(raw_health)
        anomalies = self.rca.analyze(self._snaps)
        for anomaly in anomalies:
            self._log(anomaly.agent_id, anomaly.severity, "analyze",
                      f"Anomali: {anomaly.anomaly} — {anomaly.evidence}")
        for agent_id, snap in self._snaps.items():
            if agent_id in self.suppressed:
                continue
            if agent_id not in self._active_recoveries:
                self.suppressed.add(agent_id)  # throttle: sonraki çağrıya kadar
                # _backup_mode güncelle
                if snap.state in (AgentState.ISOLATED, AgentState.RECOVERING):
                    self._backup_mode.add(agent_id)
                elif snap.state == AgentState.HEALTHY:
                    self._backup_mode.discard(agent_id)
                await self._decide_and_act(snap)


class _DummySubTask:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.prompt   = f"Sistem tanılama: {agent_id}"
        self.result   = ""
        self.status   = "running"
        self.attempts = 0

# --- Singleton ---
from core.orchestrator import orchestrator
heal_engine = SelfHealEngine(orchestrator)
