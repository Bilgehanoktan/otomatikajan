import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from services.workflow_api import repair_lab_router
from services.workflow_api.repair_lab_router import _lineage_to_improvement


def _lineage(meta_data, outcome="REPAIRED"):
    return SimpleNamespace(
        id="a30c04c3-9c9e-420b-845c-9f2a736be466",
        decision_type="RUNTIME_REPAIR_ATTEMPT",
        component_name="runtime_diagnostics",
        rationale="Runtime repair action requested.",
        outcome=outcome,
        meta_data=meta_data,
        trigger_event={"diagnostic_id": "trigger_event_diagnostic"},
        created_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
    )


def test_runtime_repair_improvement_maps_repaired_to_completed():
    item = _lineage(
        {
            "status": "completed",
            "success": True,
            "diagnostic_id": "active_error_fingerprints",
            "actions": ["resolved_fingerprints=2"],
            "requires_operator_action": False,
        }
    )

    mapped = _lineage_to_improvement(item)

    assert mapped["status"] == "completed"
    assert mapped["diagnostic_id"] == "active_error_fingerprints"
    assert mapped["actions"] == ["resolved_fingerprints=2"]
    assert mapped["requires_operator_action"] is False


def test_runtime_repair_improvement_maps_operator_required_payload():
    item = _lineage(
        {
            "payload": {
                "status": "requires_operator_action",
                "diagnostic_id": "db_fallback_active",
                "actions": [],
                "requires_operator_action": True,
            }
        },
        outcome="OPERATOR_REQUIRED",
    )

    mapped = _lineage_to_improvement(item)

    assert mapped["status"] == "action_required"
    assert mapped["diagnostic_id"] == "db_fallback_active"
    assert mapped["requires_operator_action"] is True


def test_runtime_repair_improvement_reads_diagnostic_from_trigger_event():
    item = _lineage({"status": "completed", "success": True})

    mapped = _lineage_to_improvement(item)

    assert mapped["diagnostic_id"] == "trigger_event_diagnostic"


def test_taskflow_trace_artifacts_are_visible_to_repair_lab_dashboard(tmp_path, monkeypatch):
    incident_dir = tmp_path / "INC-TASKFLOW"
    incident_dir.mkdir()
    trace_path = incident_dir / "taskflow_trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "workflow_run": {
                    "workflow_id": "self_repair_v1",
                    "workflow_name": "Egemen YAZ Self Repair Workflow",
                    "incident_id": "INC-TASKFLOW",
                    "trace_id": "TRACE-TASKFLOW",
                    "status": "WAITING_HUMAN",
                    "current_step": "approval_gate",
                    "risk_score": 0.61,
                    "final_decision": "QUORUM_REQUIRED",
                    "steps": [
                        {
                            "step_id": "build_repair_case",
                            "step_type": "deterministic",
                            "status": "SUCCEEDED",
                            "attempts": 1,
                        },
                        {
                            "step_id": "approval_gate",
                            "step_type": "human_gate",
                            "status": "SUCCEEDED",
                            "attempts": 1,
                        },
                    ],
                    "events": [
                        {
                            "event_name": "taskflow.gate.waiting",
                            "workflow_id": "self_repair_v1",
                            "step_id": "approval_gate",
                            "incident_id": "INC-TASKFLOW",
                        }
                    ],
                    "artifacts": [{"path": "repair_report.json"}],
                },
                "metrics": [{"step_id": "approval_gate", "duration_seconds": 0.1}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(repair_lab_router, "REPAIR_OUTPUTS_DIR", tmp_path)

    runs = repair_lab_router._load_taskflow_runs(limit=10)

    assert len(runs) == 1
    assert runs[0]["incident_id"] == "INC-TASKFLOW"
    assert runs[0]["workflow_id"] == "self_repair_v1"
    assert runs[0]["status"] == "WAITING_HUMAN"
    assert runs[0]["gate_waiting"] is True
    assert runs[0]["succeeded_step_count"] == 2
    assert runs[0]["artifact_count"] == 1


def test_self_repair_runs_include_real_pr_and_evidence_assets(tmp_path, monkeypatch):
    incident_dir = tmp_path / "INC-UI"
    incident_dir.mkdir()
    (incident_dir / "repair_report.json").write_text(
        json.dumps(
            {
                "repair_case": {
                    "incident_id": "INC-UI",
                    "summary": "Repair Lab blank page",
                    "suspected_files": ["apps/refine_control_plane/src/app/repair-lab/page.tsx"],
                },
                "risk_decision": {"risk_level": "LOW", "recommended_action": "DRAFT_PR_ALLOWED"},
                "sandbox_result": {"tests_passed": True, "patch_applied": True},
                "candidate": {
                    "changed_files": ["apps/refine_control_plane/src/app/repair-lab/page.tsx"],
                    "patch_path": str(incident_dir / "patch.diff"),
                },
                "final_status": "DRAFT_PR_READY",
            }
        ),
        encoding="utf-8",
    )
    (incident_dir / "draft_pr.json").write_text(
        json.dumps(
            {
                "pr_url": "https://github.com/acme/repo/pull/123",
                "title": "fix: repair lab blank page",
                "branch_name": "codex/repair-inc-ui",
            }
        ),
        encoding="utf-8",
    )
    screenshot = incident_dir / "dashboard-repair-lab-visible.png"
    screenshot.write_bytes(b"fake-png")
    monkeypatch.setattr(repair_lab_router, "REPAIR_OUTPUTS_DIR", tmp_path)

    runs = repair_lab_router._load_self_repair_reports(limit=10)

    assert len(runs) == 1
    assert runs[0]["incident_id"] == "INC-UI"
    assert runs[0]["pr_url"] == "https://github.com/acme/repo/pull/123"
    assert runs[0]["pr_title"] == "fix: repair lab blank page"
    assert runs[0]["branch_name"] == "codex/repair-inc-ui"
    assert runs[0]["evidence"][0]["url"] == "/api/v1/repair-lab/artifacts/INC-UI/dashboard-repair-lab-visible.png"


def test_repair_artifact_path_is_scoped_to_incident_dir(tmp_path, monkeypatch):
    incident_dir = tmp_path / "INC-SAFE"
    incident_dir.mkdir()
    artifact = incident_dir / "visible.png"
    artifact.write_bytes(b"fake-png")
    monkeypatch.setattr(repair_lab_router, "REPAIR_OUTPUTS_DIR", tmp_path)

    resolved = repair_lab_router._safe_repair_artifact_path("INC-SAFE", "visible.png")

    assert resolved == artifact.resolve()
    with pytest.raises(Exception):
        repair_lab_router._safe_repair_artifact_path("INC-SAFE", "../visible.png")


@pytest.mark.asyncio
async def test_lab_dashboard_keeps_taskflow_runs_when_improvements_fallback(monkeypatch):
    async def empty_list(*args, **kwargs):
        return []

    async def empty_matrix(*args, **kwargs):
        return {"verifiers": [], "candidates": []}

    async def broken_improvements(*args, **kwargs):
        raise RuntimeError("decision_lineage schema drift")

    monkeypatch.setattr(repair_lab_router, "list_benchmarks", empty_list)
    monkeypatch.setattr(repair_lab_router, "list_tournaments", empty_list)
    monkeypatch.setattr(repair_lab_router, "get_verifier_matrix", empty_matrix)
    monkeypatch.setattr(repair_lab_router, "_fetch_improvements", broken_improvements)
    monkeypatch.setattr(repair_lab_router, "_load_self_repair_reports", lambda limit=20: [])
    monkeypatch.setattr(
        repair_lab_router,
        "_load_taskflow_runs",
        lambda limit=20: [{"workflow_id": "self_repair_v1", "status": "WAITING_HUMAN"}],
    )

    dashboard = await repair_lab_router.get_lab_dashboard()

    assert dashboard["improvements"] == []
    assert dashboard["taskflow_runs"] == [{"workflow_id": "self_repair_v1", "status": "WAITING_HUMAN"}]
