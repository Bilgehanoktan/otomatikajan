from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from scripts.ops.production_handover import run_production_handover
from services.workflow_api.governance_router import trigger_handover


REPO_ROOT = Path(__file__).resolve().parents[2]
API_TS = REPO_ROOT / "apps" / "refine_control_plane" / "src" / "lib" / "api.ts"
DASHBOARD_PANEL_TSX = (
    REPO_ROOT / "apps" / "refine_control_plane" / "src" / "components" / "dashboard" / "DashboardCommandPanel.tsx"
)
COMPAT_ROUTER_PY = REPO_ROOT / "services" / "workflow_api" / "compatibility_router.py"


@pytest.mark.asyncio
async def test_run_production_handover_raises_runtime_error_when_gate_fails(monkeypatch):
    monkeypatch.setattr(
        "scripts.ops.production_handover.LaunchGatekeeper.validate_for_rollout",
        AsyncMock(return_value=(False, {"release_gate": {"status": "FAIL"}})),
    )

    with pytest.raises(RuntimeError, match="HANDOVER_ABORTED"):
        await run_production_handover("SOV-PILOT-01", True)


@pytest.mark.asyncio
async def test_trigger_handover_maps_runtime_error_to_http_409(monkeypatch):
    monkeypatch.setattr(
        "scripts.ops.production_handover.run_production_handover",
        AsyncMock(side_effect=RuntimeError("HANDOVER_ABORTED: gate failed")),
    )

    with pytest.raises(HTTPException) as exc:
        await trigger_handover("SOV-PILOT-01", True, {"id": "operator-1"})

    assert exc.value.status_code == 409
    assert exc.value.detail == "HANDOVER_ABORTED: gate failed"


def test_dashboard_command_panel_uses_body_for_drill_and_audit_actions():
    source = DASHBOARD_PANEL_TSX.read_text(encoding="utf-8")

    assert 'handleAction("drill", "/governance/drills/trigger", "POST", { scenario: "RESILIENCE_DRILL_01" })' in source
    assert 'handleAction("audit", "/compliance/audit-bundles", "POST", {' in source
    assert 'purpose: "AUDIT"' in source
    assert "/governance/drills/trigger?scenario=RESILIENCE_DRILL_01" not in source


def test_api_client_has_non_string_error_detail_coercion():
    source = API_TS.read_text(encoding="utf-8")

    assert "const coerceApiErrorDetail = (rawDetail: unknown): string => {" in source
    assert "const normalizeApiErrorDetail = (status: number, rawDetail: unknown): string => {" in source
    assert "jsonErr.detail ?? jsonErr.msg ?? jsonErr.error ?? jsonErr.message ?? raw" in source


def test_compatibility_router_parses_audit_bundle_request_body():
    source = COMPAT_ROUTER_PY.read_text(encoding="utf-8")

    assert "from services.workflow_api.governance_router import AuditBundleCreate" in source
    assert "req: AuditBundleCreate" in source
    assert "return await create_audit_bundle_endpoint(req, identity)" in source
