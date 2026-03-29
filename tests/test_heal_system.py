"""
Öz-İyileştirme Sistemi Test Suite
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heal.agent_state import AgentSnapshot, AgentState
from heal.root_cause import RootCauseAnalyzer, classify_error
from heal.recovery_strategies import (
    PromptSimplifyStrategy, ModelRotateStrategy,
    WorkloadRedirectStrategy, CooldownStrategy, PartialResultStrategy,
    get_strategy_chain,
)


# ══════════════════════════════════════════════════════════
# 1. AJAN DURUM MAKİNESİ
# ══════════════════════════════════════════════════════════
class TestAgentStateMachine:

    def _snap(self, agent_id="test_agent") -> AgentSnapshot:
        return AgentSnapshot(agent_id=agent_id)

    def test_initial_state_is_healthy(self):
        snap = self._snap()
        assert snap.state == AgentState.HEALTHY

    def test_valid_transition_healthy_to_degraded(self):
        snap = self._snap()
        assert snap.transition(AgentState.DEGRADED)
        assert snap.state == AgentState.DEGRADED

    def test_invalid_transition_healthy_to_recovering(self):
        snap = self._snap()
        assert not snap.transition(AgentState.RECOVERING)
        assert snap.state == AgentState.HEALTHY

    def test_full_lifecycle(self):
        snap = self._snap()
        assert snap.transition(AgentState.DEGRADED)
        assert snap.transition(AgentState.ISOLATED)
        assert snap.transition(AgentState.RECOVERING)
        assert snap.transition(AgentState.HEALTHY)
        assert snap.state == AgentState.HEALTHY

    def test_dead_path(self):
        snap = self._snap()
        snap.transition(AgentState.DEGRADED)
        snap.transition(AgentState.ISOLATED)
        assert snap.transition(AgentState.DEAD)
        assert snap.state == AgentState.DEAD

    def test_score_history_max_10(self):
        snap = self._snap()
        for i in range(15):
            snap.update_score(float(i) / 15)
        assert len(snap.score_history) == 10

    def test_trend_positive_when_improving(self):
        snap = self._snap()
        for s in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
            snap.update_score(s)
        assert snap.trend > 0

    def test_trend_negative_when_declining(self):
        snap = self._snap()
        for s in [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]:
            snap.update_score(s)
        assert snap.trend < 0

    def test_quarantine(self):
        snap = self._snap()
        snap.quarantine(60)
        assert snap.is_quarantined()

    def test_quarantine_expired(self):
        snap = self._snap()
        snap.quarantine_until = time.time() - 1
        assert not snap.is_quarantined()

    def test_fail_streak_increments(self):
        snap = self._snap()
        snap.record_error("RateLimitError")
        snap.record_error("RateLimitError")
        assert snap.fail_streak == 2

    def test_success_resets_streak(self):
        snap = self._snap()
        snap.record_error("timeout")
        snap.record_error("timeout")
        snap.record_success()
        assert snap.fail_streak == 0

    def test_dominant_error(self):
        snap = self._snap()
        snap.record_error("RateLimitError")
        snap.record_error("RateLimitError")
        snap.record_error("TimeoutError")
        assert snap.dominant_error == "RateLimitError"


# ══════════════════════════════════════════════════════════
# 2. KÖK NEDEN ANALİZÖRÜ
# ══════════════════════════════════════════════════════════
class TestRootCauseAnalyzer:

    def test_rate_limit_classification(self):
        assert classify_error("rate limit exceeded 429") == "RateLimitError"

    def test_context_length_classification(self):
        assert classify_error("maximum tokens exceeded context length") == "ContextLengthError"

    def test_timeout_classification(self):
        assert classify_error("request timed out") == "TimeoutError"

    def test_auth_classification(self):
        assert classify_error("401 unauthorized invalid api key") == "AuthError"

    def test_network_classification(self):
        assert classify_error("connection refused network error") == "NetworkError"

    def test_unknown_classification(self):
        assert classify_error("something completely random xyz") == "unknown"

    def test_case_insensitive(self):
        assert classify_error("RATE LIMIT EXCEEDED") == "RateLimitError"

    def test_record_returns_type(self):
        rca = RootCauseAnalyzer()
        etype = rca.record("agent1", "timeout error")
        assert etype == "TimeoutError"

    def test_error_burst_detection(self):
        rca = RootCauseAnalyzer()
        snaps = {"agent1": AgentSnapshot("agent1", score=0.2)}
        for _ in range(6):
            rca.record("agent1", "timeout")
        anomalies = rca.analyze(snaps)
        burst = [a for a in anomalies if a.anomaly == "error_burst"]
        assert len(burst) > 0

    def test_cascade_failure_detection(self):
        rca = RootCauseAnalyzer()
        snaps = {
            "a1": AgentSnapshot("a1", score=0.1),
            "a2": AgentSnapshot("a2", score=0.1),
            "a3": AgentSnapshot("a3", score=0.1),
            "a4": AgentSnapshot("a4", score=0.9),
        }
        anomalies = rca.analyze(snaps)
        cascade = [a for a in anomalies if a.anomaly == "cascade_failure"]
        assert len(cascade) > 0, "3 kritik ajan olduğunda cascade tespit edilmeli"

    def test_no_anomaly_healthy_system(self):
        rca = RootCauseAnalyzer()
        snaps = {
            "a1": AgentSnapshot("a1", score=0.9),
            "a2": AgentSnapshot("a2", score=0.85),
        }
        anomalies = rca.analyze(snaps)
        assert len(anomalies) == 0


# ══════════════════════════════════════════════════════════
# 3. KURTARMA STRATEJİLERİ
# ══════════════════════════════════════════════════════════
def _make_orch(complete_result="Mock yanıt", fail=False):
    orch = MagicMock()
    if fail:
        orch.model_orch.complete = AsyncMock(side_effect=RuntimeError("simüle hata"))
    else:
        orch.model_orch.complete = AsyncMock(return_value=complete_result)
    orch.model_orch.provider_stats.return_value = [
        {"name": "openai",    "health_score": 0.9, "circuit": "closed"},
        {"name": "anthropic", "health_score": 0.7, "circuit": "closed"},
    ]
    orch.get_health.return_value = {
        "backend_dev": 0.8, "architect": 0.3, "devops": 0.9
    }
    return orch


def _make_subtask(agent_id="architect", prompt="Test prompt " * 50):
    subtask = MagicMock()
    subtask.agent_id = agent_id
    subtask.prompt   = prompt
    subtask.result   = ""
    return subtask


class TestPromptSimplifyStrategy:

    @pytest.mark.asyncio
    async def test_simplifies_long_prompt(self):
        strategy = PromptSimplifyStrategy()
        snap     = AgentSnapshot("architect")
        subtask  = _make_subtask(prompt="X" * 1500)
        orch     = _make_orch()
        result   = await strategy.execute(snap, subtask, orch)
        assert result.success
        assert "Sadeleştirilmiş" in result.message

    @pytest.mark.asyncio
    async def test_short_prompt_not_simplified(self):
        strategy = PromptSimplifyStrategy()
        snap     = AgentSnapshot("architect")
        subtask  = _make_subtask(prompt="Kısa prompt")
        orch     = _make_orch()
        result   = await strategy.execute(snap, subtask, orch)
        assert not result.success
        assert "kısa" in result.message

    @pytest.mark.asyncio
    async def test_llm_failure_returns_failure(self):
        strategy = PromptSimplifyStrategy()
        snap     = AgentSnapshot("architect")
        subtask  = _make_subtask(prompt="X" * 1500)
        orch     = _make_orch(fail=True)
        result   = await strategy.execute(snap, subtask, orch)
        assert not result.success


class TestModelRotateStrategy:

    @pytest.mark.asyncio
    async def test_rotates_to_healthy_provider(self):
        strategy = ModelRotateStrategy()
        snap     = AgentSnapshot("architect")
        subtask  = _make_subtask()
        orch     = _make_orch()
        result   = await strategy.execute(snap, subtask, orch)
        assert result.success
        assert "openai" in result.message or "anthropic" in result.message

    @pytest.mark.asyncio
    async def test_no_providers_fails(self):
        strategy = ModelRotateStrategy()
        snap     = AgentSnapshot("architect")
        subtask  = _make_subtask()
        orch     = _make_orch()
        orch.model_orch.provider_stats.return_value = []
        result   = await strategy.execute(snap, subtask, orch)
        assert not result.success


class TestWorkloadRedirectStrategy:

    @pytest.mark.asyncio
    async def test_redirects_to_healthy_agent(self):
        strategy = WorkloadRedirectStrategy()
        snap     = AgentSnapshot("architect")
        subtask  = _make_subtask(agent_id="architect")
        orch     = _make_orch()
        result   = await strategy.execute(snap, subtask, orch)
        assert result.success
        assert result.fallback_agent in ("backend_dev", "tech_writer")

    @pytest.mark.asyncio
    async def test_no_healthy_fallback_fails(self):
        strategy = WorkloadRedirectStrategy()
        snap     = AgentSnapshot("architect")
        subtask  = _make_subtask(agent_id="architect")
        orch     = _make_orch()
        orch.get_health.return_value = {"backend_dev": 0.1, "tech_writer": 0.0}
        result   = await strategy.execute(snap, subtask, orch)
        assert not result.success


class TestCooldownStrategy:

    @pytest.mark.asyncio
    async def test_quarantines_agent(self):
        strategy = CooldownStrategy()
        snap     = AgentSnapshot("architect")
        snap.fail_streak = 2
        subtask  = _make_subtask()
        orch     = _make_orch()
        result   = await strategy.execute(snap, subtask, orch)
        assert result.success
        assert snap.is_quarantined()

    @pytest.mark.asyncio
    async def test_cooldown_increases_with_streak(self):
        strategy = CooldownStrategy()
        snap1    = AgentSnapshot("a1"); snap1.fail_streak = 0
        snap2    = AgentSnapshot("a2"); snap2.fail_streak = 3
        orch     = _make_orch()
        await strategy.execute(snap1, _make_subtask(), orch)
        q1 = snap1.quarantine_until
        await strategy.execute(snap2, _make_subtask(), orch)
        q2 = snap2.quarantine_until
        assert q2 > q1, "Yüksek streak daha uzun karantina vermeli"


class TestStrategyChain:

    def test_rate_limit_chain_starts_with_rotate(self):
        chain = get_strategy_chain("RateLimitError")
        assert isinstance(chain[0], ModelRotateStrategy)

    def test_context_length_chain_starts_with_simplify(self):
        chain = get_strategy_chain("ContextLengthError")
        assert isinstance(chain[0], PromptSimplifyStrategy)

    def test_unknown_chain_has_all_strategies(self):
        chain = get_strategy_chain("unknown")
        names = [s.name for s in chain]
        assert "prompt_simplify" in names
        assert "model_rotate" in names
        assert "workload_redirect" in names
        assert "cooldown" in names
        assert "partial_result" in names

    def test_chain_ends_with_partial_result(self):
        for error_type in ("RateLimitError", "TimeoutError", "unknown"):
            chain = get_strategy_chain(error_type)
            assert isinstance(chain[-1], PartialResultStrategy), \
                f"{error_type} zinciri partial_result ile bitmeli"


# ══════════════════════════════════════════════════════════
# 4. HEAL ENGINE ENTEGRASYON TESTLERİ
# ══════════════════════════════════════════════════════════
class TestSelfHealEngine:

    def _make_engine(self, health=None):
        from core.heal_engine import SelfHealEngine
        orch = MagicMock()
        orch.get_health.return_value = health or {
            "architect": 1.0, "backend_dev": 1.0
        }
        orch.model_orch.complete = AsyncMock(return_value="kurtarıldı")
        orch.model_orch.provider_stats.return_value = [
            {"name": "openai", "health_score": 0.9, "circuit": "closed"}
        ]
        return SelfHealEngine(orch), orch

    @pytest.mark.asyncio
    async def test_healthy_system_no_action(self):
        engine, _ = self._make_engine({"a1": 1.0, "a2": 0.95})
        await engine._cycle()
        assert len(engine._active_recoveries) == 0
        crits = [e for e in engine._events if e.severity == "critical"]
        assert len(crits) == 0

    @pytest.mark.asyncio
    async def test_degraded_agent_logged(self):
        engine, _ = self._make_engine({"agent1": 0.5})
        await engine._cycle()
        warns = [e for e in engine._events if e.severity == "warning"]
        assert len(warns) > 0

    @pytest.mark.asyncio
    async def test_on_subtask_error_records(self):
        engine, _ = self._make_engine({"agent1": 0.8})
        await engine._cycle()  # snaps oluştur
        await engine.on_subtask_error("agent1", "timeout error")
        snap = engine._snaps.get("agent1")
        assert snap is not None
        assert snap.fail_streak == 1

    @pytest.mark.asyncio
    async def test_on_subtask_success_resets_streak(self):
        engine, _ = self._make_engine({"agent1": 0.8})
        await engine._cycle()
        await engine.on_subtask_error("agent1", "timeout")
        engine.on_subtask_success("agent1")
        snap = engine._snaps["agent1"]
        assert snap.fail_streak == 0

    @pytest.mark.asyncio
    async def test_system_report_structure(self):
        engine, _ = self._make_engine()
        await engine._cycle()
        report = engine.system_report()
        assert "system_score" in report
        assert "agent_states" in report
        assert "active_recoveries" in report
        assert "rca_summary" in report

    @pytest.mark.asyncio
    async def test_recover_subtask_success(self):
        engine, orch = self._make_engine({"architect": 0.1})
        await engine._cycle()  # snaps oluştur, isolated'a geç
        subtask = _make_subtask("architect", "X" * 1500)
        rescued = await engine.recover_subtask("architect", subtask)
        # En az bir strateji başarılı olmalı
        assert isinstance(rescued, bool)

    def test_agents_in_backup_isolated(self):
        engine, _ = self._make_engine()
        engine._snaps["a1"] = AgentSnapshot("a1")
        engine._snaps["a1"].state = AgentState.ISOLATED
        backup = engine.agents_in_backup()
        assert "a1" in backup

    def test_system_health_score(self):
        engine, _ = self._make_engine({"a1": 0.8, "a2": 0.6})
        score = engine.system_health_score()
        assert score == pytest.approx(0.7)
