import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from packages.orchestration.agi.cognitive.compactor import ContextCompactor
from packages.orchestration.agi.operational.tool_weaver import ToolWeaver
from packages.orchestration.agi.operational.motor_subsystem import MotorSubsystem
from packages.orchestration.agi.schemas import ActionRecord, PlanStep, ExecutionPlan

@pytest.mark.asyncio
async def test_context_compactor_logic():
    # Mock model_orch
    mock_orch = MagicMock()
    # complete_task is called (from orchestrator context, but compactor uses it)
    mock_orch.complete_task = AsyncMock(return_value=MagicMock(content="Özet: İşlem tamamlandı."))
    
    compactor = ContextCompactor(model_orch=mock_orch)
    history = [
        ActionRecord(tool_used="test_tool", success=True, output_data="Some result")
        for _ in range(3)
    ]
    
    summary = await compactor.compact(history, "Test Goal")
    assert "Özet" in summary
    assert mock_orch.complete_task.called

@pytest.mark.asyncio
async def test_tool_weaver_self_correction_flow():
    # ModelOrchestrator'ı düzgünce mock'la
    mock_orch = MagicMock()
    
    # complete_task bir coroutine olmalı
    async def mock_complete(*args, **kwargs):
        if mock_complete.call_count == 0:
            mock_complete.call_count += 1
            return MagicMock(content="---CODESTART---def main(p): raise ValueError('Fail')---CODEEND------DOCSTART---doc---DOCEND---")
        return MagicMock(content="---CODESTART---def main(p): return {'ok': True}---CODEEND------DOCSTART---doc---DOCEND---")
    
    mock_complete.call_count = 0
    mock_orch.complete_task = mock_complete
    
    weaver = ToolWeaver(model_orch=mock_orch)
    # Sandbox'ı mock'la
    weaver.sandbox.run_python = AsyncMock(side_effect=[
        MagicMock(success=False, stderr="ValueError: Fail"),
        MagicMock(success=True, stdout="---TEST_SUCCESS---")
    ])
    
    # Registry.register'ı da mock'la ki dosya yazmasın
    weaver.registry.register = MagicMock()
    
    result = await weaver.weave_capability("Fix me requirement", max_attempts=2)
    assert result["status"] == "success"
    assert result["attempts"] == 2

@pytest.mark.asyncio
async def test_motor_subsystem_local_retry():
    # MotorSubsystem retries test
    motor = MotorSubsystem(agents={})
    
    # Sandbox mock
    mock_fail = MagicMock(success=False, stderr="Transient Error")
    mock_success = MagicMock(success=True, stdout="---RESULT_START---\n{\"ok\": true}\n---RESULT_END---")
    motor.sandbox.run_python = AsyncMock(side_effect=[mock_fail, mock_success])
    
    # Registry mock
    from packages.orchestration.agi.operational.tool_weaver import tool_registry
    tool_registry.get_tool = MagicMock(return_value={"path": "dummy.py"})
    
    step = PlanStep(step_id="s1", agent_id="dynamic_tool", action="run", params={})
    
    # open() fonksiyonunu patch ile güvenli mock'la
    with patch("builtins.open", MagicMock()):
        # Mock'lanan open'ın read() dönüşünü ayarla
        with patch("packages.orchestration.agi.operational.motor_subsystem.open") as mock_file_open:
            mock_file_open.return_value.__enter__.return_value.read.return_value = "def main(p): pass"
            record = await motor._execute_motor_step(step, "plan-123")
            assert record.success is True
            assert motor.sandbox.run_python.call_count == 2
