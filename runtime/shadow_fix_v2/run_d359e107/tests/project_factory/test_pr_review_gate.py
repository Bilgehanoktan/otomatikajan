"""Tests for PR Review Gate orchestrator."""
import pytest
from unittest.mock import MagicMock
from services.project_factory.models import (
    ProjectFactoryIntake, RequirementGate,
    PrReviewRunRequest, PrAgentReview, VerifierMeshReport,
    PrReviewScorecard, VerifierCheck,
)
from services.project_factory.pr_review_gate import run_pr_review_gate


def _make_fixtures():
    brief = ProjectFactoryIntake(
        project_id="PF-1", source_suggestion_id="1", audit_run_id="2",
        title="Title", problem_statement="P", recommended_action="R",
        status="PR_CREATED_WAITING_REVIEW",
    )
    gate = RequirementGate(status="PR_CREATED_WAITING_REVIEW")
    return brief, gate


def test_pr_review_gate_clean_pass(monkeypatch, tmp_path):
    """Full clean review → PR_REVIEW_PASSED."""
    brief, gate = _make_fixtures()

    monkeypatch.setattr("services.project_factory.pr_review_gate.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_review_gate.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.load_draft_pr_creation", lambda p, r: {
        "pr_url": "https://github.com/org/repo/pull/1",
    })
    monkeypatch.setattr("services.project_factory.pr_review_gate.write_pr_review_report", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.record_pr_review_decision", lambda **kw: None)

    # Clean PR-Agent review
    monkeypatch.setattr("services.project_factory.pr_review_gate.run_pr_agent_review", lambda p, r: PrAgentReview(
        status="PASSED", summary="All clean.", findings=[], suggestions=[],
    ))
    # Clean Verifier Mesh
    monkeypatch.setattr("services.project_factory.pr_review_gate.run_verifier_mesh", lambda p, r: VerifierMeshReport(
        status="PASSED", checks=[VerifierCheck(name="production_apply_guard", status="PASSED")],
    ))
    # Clean scorecard
    monkeypatch.setattr("services.project_factory.pr_review_gate.compute_pr_review_scorecard", lambda p, a, v, r: PrReviewScorecard(
        risk_score=0, quality_score=100, blocking_count=0, warning_count=0, verifier_pass_rate=1.0,
    ))

    req = PrReviewRunRequest(operator_id="op", rationale="running review", risk_acknowledgement=True)
    result = run_pr_review_gate("PF-1", req, str(tmp_path))

    assert result.status == "PR_REVIEW_PASSED"
    assert result.recommended_decision == "MARK_REVIEWED"
    assert result.pr_url == "https://github.com/org/repo/pull/1"
    assert result.fallback_mode is False
    assert len(result.blocking_findings) == 0


def test_pr_review_gate_blocked_by_findings(monkeypatch, tmp_path):
    """Blocking findings → PR_REVIEW_BLOCKED."""
    brief, gate = _make_fixtures()

    monkeypatch.setattr("services.project_factory.pr_review_gate.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_review_gate.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.load_draft_pr_creation", lambda p, r: {"pr_url": ""})
    monkeypatch.setattr("services.project_factory.pr_review_gate.write_pr_review_report", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.record_pr_review_decision", lambda **kw: None)

    from services.project_factory.models import PrAgentFinding
    monkeypatch.setattr("services.project_factory.pr_review_gate.run_pr_agent_review", lambda p, r: PrAgentReview(
        status="BLOCKED", summary="Merge detected.",
        findings=[PrAgentFinding(category="safety_violation", severity="blocking", description="merge_performed is true")],
    ))
    monkeypatch.setattr("services.project_factory.pr_review_gate.run_verifier_mesh", lambda p, r: VerifierMeshReport(
        status="PASSED", checks=[VerifierCheck(name="production_apply_guard", status="PASSED")],
    ))
    monkeypatch.setattr("services.project_factory.pr_review_gate.compute_pr_review_scorecard", lambda p, a, v, r: PrReviewScorecard(
        risk_score=30, quality_score=76, blocking_count=1,
    ))

    req = PrReviewRunRequest(operator_id="op", rationale="running review", risk_acknowledgement=True)
    result = run_pr_review_gate("PF-1", req, str(tmp_path))

    assert result.status == "PR_REVIEW_BLOCKED"
    assert result.recommended_decision == "BLOCK"
    assert len(result.blocking_findings) > 0


def test_pr_review_gate_blocked_by_verifier(monkeypatch, tmp_path):
    """Verifier FAILED check → PR_REVIEW_BLOCKED."""
    brief, gate = _make_fixtures()

    monkeypatch.setattr("services.project_factory.pr_review_gate.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_review_gate.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.load_draft_pr_creation", lambda p, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.write_pr_review_report", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.record_pr_review_decision", lambda **kw: None)

    monkeypatch.setattr("services.project_factory.pr_review_gate.run_pr_agent_review", lambda p, r: PrAgentReview(
        status="PASSED", summary="Clean.", findings=[],
    ))
    monkeypatch.setattr("services.project_factory.pr_review_gate.run_verifier_mesh", lambda p, r: VerifierMeshReport(
        status="FAILED", checks=[VerifierCheck(name="merge_guard", status="FAILED", detail="merge_performed=true")],
    ))
    monkeypatch.setattr("services.project_factory.pr_review_gate.compute_pr_review_scorecard", lambda p, a, v, r: PrReviewScorecard(
        risk_score=25, quality_score=80,
    ))

    req = PrReviewRunRequest(operator_id="op", rationale="running review", risk_acknowledgement=True)
    result = run_pr_review_gate("PF-1", req, str(tmp_path))

    assert result.status == "PR_REVIEW_BLOCKED"
    assert any("merge_guard" in bf for bf in result.blocking_findings)
    assert result.fallback_mode is True


def test_pr_review_gate_fallback_mode_no_pr(monkeypatch, tmp_path):
    """No draft PR URL → fallback_mode=True."""
    brief, gate = _make_fixtures()

    monkeypatch.setattr("services.project_factory.pr_review_gate.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_review_gate.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.load_draft_pr_creation", lambda p, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.write_pr_review_report", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_review_gate.record_pr_review_decision", lambda **kw: None)

    monkeypatch.setattr("services.project_factory.pr_review_gate.run_pr_agent_review", lambda p, r: PrAgentReview(
        status="PASSED", summary="Clean.", findings=[],
    ))
    monkeypatch.setattr("services.project_factory.pr_review_gate.run_verifier_mesh", lambda p, r: VerifierMeshReport(
        status="PASSED", checks=[],
    ))
    monkeypatch.setattr("services.project_factory.pr_review_gate.compute_pr_review_scorecard", lambda p, a, v, r: PrReviewScorecard())

    req = PrReviewRunRequest(operator_id="op", rationale="running review", risk_acknowledgement=True)
    result = run_pr_review_gate("PF-1", req, str(tmp_path))

    assert result.fallback_mode is True
    assert result.status == "PR_REVIEW_PASSED"


def test_pr_review_gate_invalid_state_rejects(monkeypatch, tmp_path):
    """Cannot run from wrong state."""
    brief = ProjectFactoryIntake(
        project_id="PF-1", source_suggestion_id="1", audit_run_id="2",
        title="T", problem_statement="P", recommended_action="R",
        status="SCOPE_APPROVED",
    )
    gate = RequirementGate(status="SCOPE_APPROVED")

    monkeypatch.setattr("services.project_factory.pr_review_gate.load_project_factory_artifacts", lambda p, r: (brief, gate))

    req = PrReviewRunRequest(operator_id="op", rationale="running review", risk_acknowledgement=True)
    with pytest.raises(ValueError, match="Cannot run PR review"):
        run_pr_review_gate("PF-1", req, str(tmp_path))


def test_pr_review_gate_risk_ack_required(monkeypatch, tmp_path):
    """risk_acknowledgement=false rejected."""
    req = PrReviewRunRequest(operator_id="op", rationale="running review", risk_acknowledgement=False)
    with pytest.raises(ValueError, match="acknowledge risks"):
        run_pr_review_gate("PF-1", req, str(tmp_path))
