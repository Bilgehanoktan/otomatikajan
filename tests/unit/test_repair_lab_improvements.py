from datetime import datetime, timezone
from types import SimpleNamespace

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
