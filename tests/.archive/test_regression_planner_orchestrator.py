from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.task_management import TaskPlanner, SubTask, TaskStatus
from core.orchestrator import Orchestrator, DAG_WORKFLOW
from quality.approval_gate import RiskLevel


def test_task_planner_should_embed_contract_fields_in_every_prompt():
    """
    Yeni AGENT_CONTRACTS prompt'ları gerçekten sözleşme alanlarını taşıyor mu?
    """
    planner = TaskPlanner()
    subtasks = planner.plan(
        title="Kripto analiz dashboard",
        description="Gerçek zamanlı veri, alarm ve raporlama",
    )

    assert subtasks, "Planner en az bir subtask üretmeli"

    for st in subtasks:
        assert "Senin Uzmanlığın:" in st.prompt
        assert "Kapsam Sınırın" in st.prompt
        assert "Senden Beklenen Kesin Çıktı Formatı" in st.prompt
        assert "Talimat: Bu projeye SADECE kendi rolün" in st.prompt


def test_dag_workflow_should_not_reference_unplanned_agents():
    """
    Planner ile DAG haritası tutarlı olmalı.
    DAG'ta geçen her ajan planner tarafından üretilebilmeli.

    Bu test şu an FAIL edebilir çünkü system_controller DAG'ta var,
    ama planner contract'larında yok.
    """
    planner_agents = set(TaskPlanner.AGENT_CONTRACTS.keys())
    dag_agents = set(DAG_WORKFLOW.keys())

    missing_in_planner = dag_agents - planner_agents

    assert not missing_in_planner, (
        "DAG'ta tanımlı ama planner tarafından üretilmeyen ajan(lar) var: "
        f"{sorted(missing_in_planner)}"
    )


@pytest.mark.asyncio
async def test_run_subtask_should_not_call_context_builder_when_memory_disabled(monkeypatch):
    """
    _memory_enabled=False ise context_builder.build_context çağrılmamalı.
    """
    orch = Orchestrator()
    orch._memory_enabled = False
    orch._quality_enabled = False
    orch._reviewer_enabled = False
    orch._health = {"architect": 1.0}

    fake_agent = AsyncMock()
    fake_agent.execute.return_value = SimpleNamespace(raw_output="normal çıktı")
    orch._agents = {"architect": fake_agent}

    async def _risk_low(_prompt: str):
        return RiskLevel.LOW

    async def _should_not_run(*args, **kwargs):
        raise AssertionError("Memory disabled iken context_builder çağrılmamalı")

    monkeypatch.setattr(orch, "_evaluate_risk_semantically", _risk_low)
    monkeypatch.setattr(
        "core.orchestrator.context_builder.build_context",
        _should_not_run,
        raising=True,
    )
    monkeypatch.setattr(
        "core.orchestrator.output_parser.parse",
        lambda agent_id, raw: SimpleNamespace(summary="özet", agent_id=agent_id),
        raising=True,
    )

    st = SubTask(id="st-1", agent_id="architect", prompt="mimari çıkar")

    await orch._run_subtask(st, shared_context="")

    assert st.status == TaskStatus.DONE
    assert st.result == "özet"
    fake_agent.execute.assert_called_once()


@pytest.mark.asyncio
async def test_run_subtask_should_skip_quality_pipeline_when_quality_disabled(monkeypatch):
    """
    _quality_enabled=False ise:
    - lint entegrasyonu
    - _check_quality
    - reviewer
    çalışmamalı.
    """
    orch = Orchestrator()
    orch._memory_enabled = False
    orch._quality_enabled = False
    orch._reviewer_enabled = False
    orch._health = {"architect": 1.0}

    fake_agent = AsyncMock()
    fake_agent.execute.return_value = SimpleNamespace(raw_output="def foo():\n    return 1")
    orch._agents = {"architect": fake_agent}

    async def _risk_low(_prompt: str):
        return RiskLevel.LOW

    async def _quality_should_not_run(*args, **kwargs):
        raise AssertionError("Quality disabled iken _check_quality çağrılmamalı")

    monkeypatch.setattr(orch, "_evaluate_risk_semantically", _risk_low)
    monkeypatch.setattr(orch, "_check_quality", _quality_should_not_run)
    monkeypatch.setattr(
        "core.orchestrator.output_parser.parse",
        lambda agent_id, raw: SimpleNamespace(summary="kod özeti", agent_id=agent_id),
        raising=True,
    )

    st = SubTask(id="st-2", agent_id="architect", prompt="örnek python kodu üret")

    await orch._run_subtask(st, shared_context="")

    assert st.status == TaskStatus.DONE
    assert st.quality_score is None
    assert st.reviewed is False
    fake_agent.execute.assert_called_once()
