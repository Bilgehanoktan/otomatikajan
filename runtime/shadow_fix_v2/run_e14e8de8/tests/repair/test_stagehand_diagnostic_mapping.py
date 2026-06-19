import json
import shutil
import pytest
from pathlib import Path
from services.repair.ui_diagnostics import UIDiagnosticRequest
from services.repair.stagehand_adapter import (
    run_stagehand_diagnostic,
    write_diagnostic_artifact,
    map_diagnostic_to_ceo_finding,
    safe_resolve_diagnostic_dir,
    calculate_priority_score
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS = WORKSPACE_ROOT / "repair_outputs"
DIAGNOSTICS_DIR = REPAIR_OUTPUTS / "diagnostics"

@pytest.fixture(autouse=True)
def clean_diagnostics():
    yield
    if DIAGNOSTICS_DIR.exists():
        shutil.rmtree(DIAGNOSTICS_DIR, ignore_errors=True)

def test_stagehand_mock_diagnostic_writes_report_artifact():
    req = UIDiagnosticRequest(
        route="/ceo",
        symptom="findings table is empty",
        mode="mock"
    )
    result = run_stagehand_diagnostic(req)
    assert result.status == "completed"
    assert "findings table is empty" in result.symptom
    
    write_diagnostic_artifact(result)
    
    diag_dir = DIAGNOSTICS_DIR / result.diagnostic_id
    assert diag_dir.exists()
    assert (diag_dir / "diagnostic_report.json").exists()
    assert (diag_dir / "network_log.json").exists()
    assert (diag_dir / "console_log.json").exists()
    assert (diag_dir / "screenshot.png").exists()

def test_network_404_maps_to_ceo_finding_endpoint_and_priority():
    req = UIDiagnosticRequest(
        route="/ceo",
        symptom="findings table is empty",
        mode="mock"
    )
    result = run_stagehand_diagnostic(req)
    finding = map_diagnostic_to_ceo_finding(result)
    
    assert finding["finding_id"] == result.diagnostic_id
    assert finding["title"] == result.symptom
    assert finding["priority_score"] == 78  # 404 rule
    assert finding["affected_route"] == "/ceo"
    assert finding["affected_endpoint"] == "/api/v1/ceo/findings"
    assert "services/workflow_api/ceo_router.py" in finding["affected_files"]
    assert finding["recommended_agent"] == "swe_agent"
    assert finding["requested_mode"] == "local_adapter"

def test_hydration_error_maps_to_ui_diagnostic_finding():
    req = UIDiagnosticRequest(
        route="/identity-trust",
        symptom="hydration mismatch",
        mode="mock"
    )
    result = run_stagehand_diagnostic(req)
    finding = map_diagnostic_to_ceo_finding(result)
    
    assert finding["priority_score"] == 72  # hydration rule
    assert finding["category"] == "ui_diagnostic"
    assert "apps/refine_control_plane/src/components/IdentityTrustCenterPanel.tsx" in finding["affected_files"]

def test_diagnostic_to_finding_defaults_to_swe_agent_local_adapter():
    req = UIDiagnosticRequest(
        route="/any-route",
        symptom="unresponsive UI button",
        mode="mock"
    )
    result = run_stagehand_diagnostic(req)
    finding = map_diagnostic_to_ceo_finding(result)
    
    assert finding["recommended_agent"] == "swe_agent"
    assert finding["requested_mode"] == "local_adapter"
    assert finding["can_trigger_repair"] is True
    assert finding["status"] == "NEW"

def test_stagehand_mode_validates_external_agent_catalog():
    # Invalid mode (e.g. bypass_human_gate) should fail catalog checks
    req = UIDiagnosticRequest(
        route="/ceo",
        symptom="empty findings",
        mode="bypass_human_gate"
    )
    with pytest.raises(ValueError, match="Agent execution validation failed for stagehand"):
        run_stagehand_diagnostic(req)

def test_diagnostic_artifact_blocks_path_traversal():
    with pytest.raises(ValueError, match="Path traversal detected in diagnostic_id"):
        safe_resolve_diagnostic_dir("../hack")
    with pytest.raises(ValueError, match="Path traversal detected in diagnostic_id"):
        safe_resolve_diagnostic_dir("sub/dir")
    with pytest.raises(ValueError, match="Path traversal detected in diagnostic_id"):
        safe_resolve_diagnostic_dir("sub\\dir")
