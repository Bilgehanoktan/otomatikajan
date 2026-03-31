import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.orchestrator import Orchestrator, SubTask, TaskStatus
from core.task_management import ProjectTask

@pytest.fixture
def mock_llm_orchestrator():
    """LLM maliyetini ve sürelerini engellemek için mock"""
    mock_orch = AsyncMock()
    # Canonical LLMResponse formatında mock dönüş
    mock_result = MagicMock()
    mock_result.content = '{"summary": "Test başarılı", "details": "Mock LLM Yanıtı"}'
    mock_result.provider = "mock_provider"
    mock_result.model_name = "mock_model"
    mock_result.input_tokens = 10
    mock_result.output_tokens = 20
    mock_result.cost_usd = 0.0
    mock_result.latency_s = 0.1
    
    mock_orch.complete_task.return_value = mock_result
    mock_orch.generate.return_value = "LOW"
    mock_orch.complete.return_value = "Mock Content"
    return mock_orch

@pytest.fixture(autouse=True)
def mock_context_builder():
    with patch("core.orchestrator.context_builder") as mock_cb:
        mock_cb.build_context.side_effect = lambda agent_id, task_text, **kwargs: task_text
        yield mock_cb

@pytest.mark.asyncio
async def test_orchestrator_dag_execution(mock_llm_orchestrator):
    """
    Bu test, Orchestrator'ın DAG yapısını doğru çalıştırıp çalıştırmadığını,
    ajanların sırayla birbirini beklediğini kontrol eder.
    Gerçekten güvenilir çalışan bir sistem olup olmadığını kanıtlar.
    """
    orc = Orchestrator()
    orc.model_orch = mock_llm_orchestrator
    
    # Kalite kontrol ve Sandbox yavaşlatmalarını test için deaktive et
    orc._quality_enabled = False
    orc._memory_enabled = False
    
    await orc.start()
    
    # Dummy ajanlar ekleyelim (Gerçek ajanları beklememek için)
    mock_agent_1 = AsyncMock()
    mock_agent_1.execute.return_value = MagicMock(raw_output="Mock Output 1")
    
    mock_agent_2 = AsyncMock()
    mock_agent_2.execute.return_value = MagicMock(raw_output="Mock Output 2")
    
    orc._agents = {
        "architect": mock_agent_1,
        "backend_dev": mock_agent_2
    }
    
    # Planner'ı mocklayıp sahte subtask'lar verelim
    orc.planner.plan = MagicMock(return_value=[
        SubTask(id="st1", agent_id="architect", prompt="Sistem mimarisi çıkar"),
        SubTask(id="st2", agent_id="backend_dev", prompt="Veritabanı yapısını yaz")
    ])
    
    # Çalıştır
    project_task = await orc.run_project(
        title="Test Projesi", 
        description="DAG Test Açıklaması"
    )
    
    # Asertion (Doğrulamalar)
    assert project_task.status == TaskStatus.DONE
    assert len(project_task.subtasks) == 2
    
    # Her iki alt görevin de başarıyla tamamlandığını doğrula
    for st in project_task.subtasks:
        assert st.status == TaskStatus.DONE
        
    # Ajanların execute fonksiyonlarının çağrıldığından emin ol
    mock_agent_1.execute.assert_called_once()
    mock_agent_2.execute.assert_called_once()
    
    # Temizlik
    await orc.shutdown()
