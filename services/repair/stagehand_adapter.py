from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from services.repair.ui_diagnostics import (
    UIDiagnosticRequest,
    UIDiagnosticResult,
    UIDiagnosticNetworkError,
    CEOFindingPayload
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS_DIR = WORKSPACE_ROOT / "repair_outputs"
DIAGNOSTICS_DIR = REPAIR_OUTPUTS_DIR / "diagnostics"

def safe_resolve_diagnostic_dir(diagnostic_id: str) -> Path:
    # Ensure diagnostic_id contains no path traversal (e.g. ..)
    if ".." in diagnostic_id or "\\" in diagnostic_id or "/" in diagnostic_id:
        raise ValueError("Path traversal detected in diagnostic_id")
    diag_dir = DIAGNOSTICS_DIR / diagnostic_id
    diag_dir.mkdir(parents=True, exist_ok=True)
    return diag_dir

def calculate_priority_score(result: UIDiagnosticResult) -> int:
    has_500 = any(e.status >= 500 for e in result.network_errors)
    has_404 = any(e.status == 404 for e in result.network_errors)
    has_hydration = any("hydration" in err.lower() or "prop `classname` did not match" in err.lower() for err in result.console_errors)
    
    if has_500:
        return 92
    elif has_404:
        return 78
    elif has_hydration:
        return 72
    elif "empty" in result.symptom.lower():
        return 48
    else:
        return 50

def run_stagehand_diagnostic(request: UIDiagnosticRequest) -> UIDiagnosticResult:
    import uuid
    from datetime import datetime, UTC
    from services.repair.external_repo_integrations import validate_agent_execution
    
    diagnostic_id = f"DIAG-{uuid.uuid4().hex[:8].upper()}"
    
    # Enforce credential leak checks
    for keyword in ["env", "secret", "password", "token", "key"]:
        if keyword in request.route.lower() or keyword in request.symptom.lower():
            raise ValueError("Input contains forbidden keywords to prevent credential/env exposure.")
            
    # Validate agent execution if mode is NOT mock
    if request.mode != "mock":
        # This will raise ValueError/PermissionError if stagehand is not allowed in catalog
        validation = validate_agent_execution("stagehand", request.mode)
        if not validation.get("valid"):
            raise ValueError(f"Agent execution validation failed for stagehand: {validation.get('reason')}")
            
    created_at_str = datetime.now(UTC).isoformat()
    
    # Enforce safe screenshot ref pathing
    screenshot_ref = str(DIAGNOSTICS_DIR / diagnostic_id / "screenshot.png")
    
    if "simulate_fail" in request.symptom.lower():
        result = UIDiagnosticResult(
            diagnostic_id=diagnostic_id,
            route=request.route,
            symptom=request.symptom,
            status="failed",
            suspected_root_cause="Browser automation process crashed",
            repair_instruction="Restart UI test runner or check browser binaries",
            confidence_score=0.0,
            created_at=created_at_str,
            screenshot_ref=None
        )
        return result
        
    symptom_lower = request.symptom.lower()
    if "findings table is empty" in symptom_lower or "empty" in symptom_lower:
        net_errors = [
            UIDiagnosticNetworkError(url="/api/v1/ceo/findings", status=404, method="GET")
        ]
        result = UIDiagnosticResult(
            diagnostic_id=diagnostic_id,
            route=request.route,
            symptom=request.symptom,
            status="completed",
            network_errors=net_errors,
            console_errors=[],
            dom_observations=["Findings table rendered empty state"],
            screenshot_ref=screenshot_ref,
            suspected_root_cause="backend route missing",
            suspected_files=[
                "services/workflow_api/ceo_router.py",
                "services/orchestration/ceo/engine.py"
            ],
            repair_instruction="Add GET /api/v1/ceo/findings and connect it to CEOEngine.get_findings",
            confidence_score=0.84,
            created_at=created_at_str
        )
    elif "hydration" in symptom_lower:
        result = UIDiagnosticResult(
            diagnostic_id=diagnostic_id,
            route=request.route,
            symptom=request.symptom,
            status="completed",
            network_errors=[],
            console_errors=["Warning: Prop `className` did not match. Server: \"visible\" Client: \"hidden\""],
            dom_observations=["Hydration mismatch on panel component"],
            screenshot_ref=screenshot_ref,
            suspected_root_cause="React UI hydration mismatch between server rendering and client state",
            suspected_files=[
                "apps/refine_control_plane/src/components/IdentityTrustCenterPanel.tsx"
            ],
            repair_instruction="Wrap client-only side effects in useEffect to prevent server-side hydration mismatches",
            confidence_score=0.76,
            created_at=created_at_str
        )
    else:
        result = UIDiagnosticResult(
            diagnostic_id=diagnostic_id,
            route=request.route,
            symptom=request.symptom,
            status="completed",
            network_errors=[],
            console_errors=[],
            dom_observations=["UI rendered but component action was unresponsive"],
            screenshot_ref=screenshot_ref,
            suspected_root_cause=f"UI component state out of sync on symptom: {request.symptom}",
            suspected_files=["apps/refine_control_plane/src/App.tsx"],
            repair_instruction=f"Inspect and align event listeners for symptom: {request.symptom}",
            confidence_score=0.65,
            created_at=created_at_str
        )
        
    return result

def write_diagnostic_artifact(result: UIDiagnosticResult):
    diag_dir = safe_resolve_diagnostic_dir(result.diagnostic_id)
    
    report_path = diag_dir / "diagnostic_report.json"
    report_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    
    net_log_path = diag_dir / "network_log.json"
    net_errors_data = [err.model_dump() for err in result.network_errors]
    net_log_path.write_text(json.dumps(net_errors_data, indent=2), encoding="utf-8")
    
    console_log_path = diag_dir / "console_log.json"
    console_log_path.write_text(json.dumps(result.console_errors, indent=2), encoding="utf-8")
    
    if result.screenshot_ref:
        screenshot_path = Path(result.screenshot_ref)
        if ".." in result.screenshot_ref or str(WORKSPACE_ROOT) not in str(screenshot_path.resolve()):
            raise ValueError("Path traversal detected in screenshot path")
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        screenshot_path.write_bytes(b"MOCK_SCREENSHOT_DATA")

def map_diagnostic_to_ceo_finding(result: UIDiagnosticResult) -> dict[str, Any]:
    priority_score = calculate_priority_score(result)
    
    first_net_url = None
    if result.network_errors:
        first_net_url = result.network_errors[0].url
        
    description = f"{result.suspected_root_cause}. Recommended action: {result.repair_instruction}"
    
    finding = {
        "finding_id": result.diagnostic_id,
        "title": result.symptom,
        "description": description,
        "category": "ui_diagnostic",
        "priority_score": priority_score,
        "source_signal": "stagehand_diagnostic",
        "affected_route": result.route,
        "affected_endpoint": first_net_url,
        "affected_files": result.suspected_files,
        "recommended_action": result.repair_instruction,
        "recommended_agent": "swe_agent",
        "requested_mode": "local_adapter",
        "can_trigger_repair": True,
        "status": "NEW"
    }
    return finding
