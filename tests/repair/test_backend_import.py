import subprocess
import sys
import pytest

def test_workflow_api_import():
    """
    Smoke test to ensure the workflow API and its routers can be imported without SyntaxError.
    This prevents routing bugs from breaking the entire backend.
    """
    cmd = [sys.executable, "-c", "import services.workflow_api.main; print('ok')"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0, f"Import failed with error: {result.stderr}"
    assert "ok" in result.stdout

def test_ui_repair_orchestrator_import():
    """Ensure orchestrator can be imported."""
    try:
        from services.repair.ui_repair_orchestrator import UIRepairOrchestrator
        assert UIRepairOrchestrator is not None
    except Exception as e:
        pytest.fail(f"UIRepairOrchestrator import failed: {e}")
