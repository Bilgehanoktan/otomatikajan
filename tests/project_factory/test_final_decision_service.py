"""Tests for Final Decision Service."""
import pytest
from services.project_factory.models import (
    ProjectFactoryIntake, RequirementGate, FinalApproveRequest, 
    FinalRejectRequest, FinalRevisionRequest, ReleaseManifest
)
from services.project_factory.final_decision_service import (
    final_approve, final_reject, final_request_revision, _validate_safety_for_approve
)


def _make_fixtures(status="READY_FOR_FINAL_OPERATOR_DECISION"):
    brief = ProjectFactoryIntake(
        project_id="PF-1", source_suggestion_id="1", audit_run_id="2",
        title="T", problem_statement="P", recommended_action="R",
        status=status,
    )
    gate = RequirementGate(status=status)
    return brief, gate


def test_final_approve_clean_pass(monkeypatch, tmp_path):
    """Final approve passes with clean safety checks."""
    brief, gate = _make_fixtures()
    
    monkeypatch.setattr("services.project_factory.final_decision_service.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.final_decision_service.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.final_decision_service.write_final_operator_decision", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.final_decision_service.record_final_decision", lambda **kw: None)
    
    # Mock safety check to return no violations
    monkeypatch.setattr("services.project_factory.final_decision_service._validate_safety_for_approve", lambda p, r: [])
    
    monkeypatch.setattr("services.project_factory.final_decision_service.build_release_archive", lambda *args, **kwargs: ReleaseManifest(
        project_id=kwargs.get("project_id", "PF-1"), release_id=kwargs.get("release_id", "REL-1"), status="RELEASE_ARCHIVE_READY", 
        final_decision="FINAL_APPROVED", approved_by=kwargs.get("operator_id", "op1"), closure_report="foo.md"
    ))
    
    req = FinalApproveRequest(operator_id="op1", rationale="approved", risk_acknowledgement=True)
    res = final_approve("PF-1", req, str(tmp_path))
    
    assert res["status"] == "PROJECT_CLOSED"
    assert brief.status == "PROJECT_CLOSED"


def test_final_approve_blocked_by_safety(monkeypatch, tmp_path):
    """Safety validation failure blocks approve."""
    brief, gate = _make_fixtures()
    monkeypatch.setattr("services.project_factory.final_decision_service.load_project_factory_artifacts", lambda p, r: (brief, gate))
    
    monkeypatch.setattr("services.project_factory.final_decision_service._validate_safety_for_approve", lambda p, r: ["merge_performed is True"])
    
    req = FinalApproveRequest(operator_id="op1", rationale="approved", risk_acknowledgement=True)
    with pytest.raises(ValueError, match="Safety validation failed"):
        final_approve("PF-1", req, str(tmp_path))


def test_validate_safety_for_approve(monkeypatch, tmp_path):
    """Tests _validate_safety_for_approve directly."""
    
    def mock_load(p, n, r):
        if n == "delivery_manifest.json":
            return {"production_apply_allowed": True} # VIOLATION
        if n == "apply_preview.json":
            return {"production_apply_performed": False}
        if n == "draft_pr_plan.json":
            return {"git_operations_performed": False}
        if n == "pr_review_report.json":
            return {"status": "PR_REVIEW_BLOCKED", "blocking_findings": ["error"]} # VIOLATIONS
        if n == "verifier_mesh_report.json":
            return {"status": "FAILED"} # VIOLATION
        return None
        
    monkeypatch.setattr("services.project_factory.final_decision_service._load_json_artifact", mock_load)
    monkeypatch.setattr("services.project_factory.final_decision_service.load_draft_pr_creation", lambda p, r: {
        "merge_performed": True, # VIOLATION
        "force_push_performed": False,
        "production_direct_write": False,
    })
    
    violations = _validate_safety_for_approve("PF-1", str(tmp_path))
    assert len(violations) >= 4
    assert any("production_apply_allowed" in v for v in violations)
    assert any("merge_performed" in v for v in violations)
    assert any("PR_REVIEW_PASSED" in v for v in violations)
    assert any("verifier_mesh_report" in v for v in violations)


def test_final_reject(monkeypatch, tmp_path):
    """Final reject changes state to FINAL_REJECTED."""
    brief, gate = _make_fixtures()
    monkeypatch.setattr("services.project_factory.final_decision_service.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.final_decision_service.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.final_decision_service.write_final_operator_decision", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.final_decision_service.record_final_decision", lambda **kw: None)
    
    req = FinalRejectRequest(operator_id="op1", rationale="rejected")
    res = final_reject("PF-1", req, str(tmp_path))
    
    assert res["status"] == "FINAL_REJECTED"
    assert brief.status == "FINAL_REJECTED"


def test_final_revision(monkeypatch, tmp_path):
    """Final revision changes state to FINAL_REVISION_REQUESTED."""
    brief, gate = _make_fixtures()
    monkeypatch.setattr("services.project_factory.final_decision_service.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.final_decision_service.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.final_decision_service.write_final_operator_decision", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.final_decision_service.record_final_decision", lambda **kw: None)
    
    req = FinalRevisionRequest(operator_id="op1", rationale="revise", revision_notes="fix it")
    res = final_request_revision("PF-1", req, str(tmp_path))
    
    assert res["status"] == "FINAL_REVISION_REQUESTED"
    assert brief.status == "FINAL_REVISION_REQUESTED"


def test_invalid_state(monkeypatch, tmp_path):
    """Cannot decide from wrong state."""
    brief, gate = _make_fixtures("PR_REVIEW_PASSED")
    monkeypatch.setattr("services.project_factory.final_decision_service.load_project_factory_artifacts", lambda p, r: (brief, gate))
    
    req = FinalApproveRequest(operator_id="op1", rationale="approved", risk_acknowledgement=True)
    with pytest.raises(ValueError, match="Cannot final approve"):
        final_approve("PF-1", req, str(tmp_path))
        
    req2 = FinalRejectRequest(operator_id="op1", rationale="reject")
    with pytest.raises(ValueError, match="Cannot final reject"):
        final_reject("PF-1", req2, str(tmp_path))
        
    req3 = FinalRevisionRequest(operator_id="op1", rationale="revise", revision_notes="notes")
    with pytest.raises(ValueError, match="Cannot request revision"):
        final_request_revision("PF-1", req3, str(tmp_path))


def test_risk_acknowledgement_required(monkeypatch, tmp_path):
    """risk_acknowledgement=false rejected."""
    req = FinalApproveRequest(operator_id="op1", rationale="approved", risk_acknowledgement=False)
    with pytest.raises(ValueError, match="acknowledge risks"):
        final_approve("PF-1", req, str(tmp_path))


def test_final_decision_logs_append_only(tmp_path):
    """Decision logs are append-only."""
    from services.project_factory.final_decision_logs import record_final_decision, get_final_decision_logs
    
    project_dir = tmp_path / "project_outputs" / "project_factory" / "PF-LOG"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    ws = str(tmp_path)
    record_final_decision("PF-LOG", "FINAL_APPROVE", "op1", "test1", workspace_root=ws)
    record_final_decision("PF-LOG", "FINAL_REJECT", "op2", "test2", workspace_root=ws)
    
    logs = get_final_decision_logs("PF-LOG", ws)
    assert len(logs) == 2
    assert logs[0]["action"] == "FINAL_APPROVE"
    assert logs[1]["action"] == "FINAL_REJECT"
