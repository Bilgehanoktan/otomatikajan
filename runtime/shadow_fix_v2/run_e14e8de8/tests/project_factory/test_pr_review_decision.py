"""Tests for PR Review Decision handler."""
import pytest
from services.project_factory.models import (
    ProjectFactoryIntake, RequirementGate, PrReviewDecisionRequest,
)
from services.project_factory.pr_review_decision import apply_pr_review_decision


def _make_fixtures(status="PR_REVIEW_PASSED"):
    brief = ProjectFactoryIntake(
        project_id="PF-1", source_suggestion_id="1", audit_run_id="2",
        title="T", problem_statement="P", recommended_action="R",
        status=status,
    )
    gate = RequirementGate(status=status)
    return brief, gate


def test_mark_reviewed_transitions_to_final(monkeypatch, tmp_path):
    """MARK_REVIEWED → READY_FOR_FINAL_OPERATOR_DECISION."""
    brief, gate = _make_fixtures("PR_REVIEW_PASSED")
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_review_decision.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_pr_review_report", lambda p, r: {"status": "PR_REVIEW_PASSED"})
    monkeypatch.setattr("services.project_factory.pr_review_decision.write_pr_review_report", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_decision.record_pr_review_decision", lambda **kw: None)

    req = PrReviewDecisionRequest(
        operator_id="op", decision="MARK_REVIEWED",
        rationale="approved after review", risk_acknowledgement=True,
    )
    result = apply_pr_review_decision("PF-1", req, str(tmp_path))
    assert result["new_status"] == "READY_FOR_FINAL_OPERATOR_DECISION"
    assert brief.status == "READY_FOR_FINAL_OPERATOR_DECISION"


def test_request_changes_transition(monkeypatch, tmp_path):
    """REQUEST_CHANGES → PR_REVIEW_REQUEST_CHANGES."""
    brief, gate = _make_fixtures("PR_REVIEW_PASSED")
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_review_decision.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_pr_review_report", lambda p, r: {"status": "PR_REVIEW_PASSED"})
    monkeypatch.setattr("services.project_factory.pr_review_decision.write_pr_review_report", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_decision.record_pr_review_decision", lambda **kw: None)

    req = PrReviewDecisionRequest(
        operator_id="op", decision="REQUEST_CHANGES",
        rationale="needs more tests", risk_acknowledgement=True,
    )
    result = apply_pr_review_decision("PF-1", req, str(tmp_path))
    assert result["new_status"] == "PR_REVIEW_REQUEST_CHANGES"


def test_block_transition(monkeypatch, tmp_path):
    """BLOCK → PR_REVIEW_BLOCKED."""
    brief, gate = _make_fixtures("PR_REVIEW_PASSED")
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_review_decision.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_pr_review_report", lambda p, r: {"status": "PR_REVIEW_PASSED"})
    monkeypatch.setattr("services.project_factory.pr_review_decision.write_pr_review_report", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_decision.record_pr_review_decision", lambda **kw: None)

    req = PrReviewDecisionRequest(
        operator_id="op", decision="BLOCK",
        rationale="security issue found", risk_acknowledgement=True,
    )
    result = apply_pr_review_decision("PF-1", req, str(tmp_path))
    assert result["new_status"] == "PR_REVIEW_BLOCKED"


def test_defer_transition(monkeypatch, tmp_path):
    """DEFER → PR_REVIEW_DEFERRED."""
    brief, gate = _make_fixtures("PR_REVIEW_PASSED")
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_review_decision.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_pr_review_report", lambda p, r: {"status": "PR_REVIEW_PASSED"})
    monkeypatch.setattr("services.project_factory.pr_review_decision.write_pr_review_report", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_decision.record_pr_review_decision", lambda **kw: None)

    req = PrReviewDecisionRequest(
        operator_id="op", decision="DEFER",
        rationale="wait for next sprint", risk_acknowledgement=True,
    )
    result = apply_pr_review_decision("PF-1", req, str(tmp_path))
    assert result["new_status"] == "PR_REVIEW_DEFERRED"


def test_invalid_decision_rejected(monkeypatch, tmp_path):
    """Invalid decision string rejected."""
    brief, gate = _make_fixtures("PR_REVIEW_PASSED")
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_project_factory_artifacts", lambda p, r: (brief, gate))

    req = PrReviewDecisionRequest(
        operator_id="op", decision="AUTO_MERGE",
        rationale="merge it now", risk_acknowledgement=True,
    )
    with pytest.raises(ValueError, match="Invalid decision"):
        apply_pr_review_decision("PF-1", req, str(tmp_path))


def test_invalid_state_rejected(monkeypatch, tmp_path):
    """Cannot decide from wrong state."""
    brief, gate = _make_fixtures("SCOPE_APPROVED")
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_project_factory_artifacts", lambda p, r: (brief, gate))

    req = PrReviewDecisionRequest(
        operator_id="op", decision="MARK_REVIEWED",
        rationale="reviewing now", risk_acknowledgement=True,
    )
    with pytest.raises(ValueError, match="Cannot apply decision"):
        apply_pr_review_decision("PF-1", req, str(tmp_path))


def test_risk_acknowledgement_required(monkeypatch, tmp_path):
    """risk_acknowledgement=false rejected."""
    brief, gate = _make_fixtures("PR_REVIEW_PASSED")
    monkeypatch.setattr("services.project_factory.pr_review_decision.load_project_factory_artifacts", lambda p, r: (brief, gate))

    req = PrReviewDecisionRequest(
        operator_id="op", decision="MARK_REVIEWED",
        rationale="reviewing now", risk_acknowledgement=False,
    )
    with pytest.raises(ValueError, match="acknowledge risks"):
        apply_pr_review_decision("PF-1", req, str(tmp_path))


def test_decision_logs_append_only(tmp_path):
    """Decision logs are append-only."""
    from services.project_factory.pr_review_logs import record_pr_review_decision, get_pr_review_decisions
    import os

    # Create project dir structure
    project_dir = tmp_path / "project_outputs" / "project_factory" / "PF-LOG"
    project_dir.mkdir(parents=True, exist_ok=True)

    ws = str(tmp_path)
    record_pr_review_decision("PF-LOG", "ACTION_A", "op1", "first", workspace_root=ws)
    record_pr_review_decision("PF-LOG", "ACTION_B", "op2", "second", workspace_root=ws)

    logs = get_pr_review_decisions("PF-LOG", ws)
    assert len(logs) == 2
    assert logs[0]["action"] == "ACTION_A"
    assert logs[1]["action"] == "ACTION_B"
    assert logs[0]["operator_id"] == "op1"
    assert logs[1]["operator_id"] == "op2"
