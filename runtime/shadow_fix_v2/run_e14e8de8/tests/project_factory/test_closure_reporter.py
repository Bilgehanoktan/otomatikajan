"""Tests for Closure Reporter."""
import pytest
from services.project_factory.closure_reporter import generate_closure_report


def test_generate_closure_report(monkeypatch, tmp_path):
    """Closure report contains expected content."""
    
    def mock_load(p, n, r):
        if n == "project_brief.json":
            return {"title": "Test Title"}
        if n == "pr_review_report.json":
            return {"status": "PR_REVIEW_PASSED", "risk_score": 10, "quality_score": 90}
        if n == "draft_pr_creation.json":
            return {"pr_url": "https://github.com/test"}
        return None
        
    monkeypatch.setattr("services.project_factory.closure_reporter._load_json_artifact", mock_load)
    
    report = generate_closure_report(
        project_id="PF-1",
        operator_id="op1",
        rationale="Looks good",
        release_id="REL-PF-1",
        copied_evidence=["file1.json", "file2.json"],
        missing_evidence=["missing.json"],
        workspace_root=str(tmp_path)
    )
    
    assert "Test Title" in report
    assert "REL-PF-1" in report
    assert "op1" in report
    assert "Looks good" in report
    assert "PR_REVIEW_PASSED" in report
    assert "file1.json" in report
    assert "missing.json" in report
    assert "https://github.com/test" in report


def test_generate_closure_report_fallback(monkeypatch, tmp_path):
    """Fallback mode note is included when draft PR creation is missing."""
    
    def mock_load(p, n, r):
        return {} # empty for everything
        
    monkeypatch.setattr("services.project_factory.closure_reporter._load_json_artifact", mock_load)
    
    report = generate_closure_report(
        project_id="PF-1",
        operator_id="op1",
        rationale="fallback test",
        release_id="REL-PF-1",
        copied_evidence=[],
        missing_evidence=[],
        workspace_root=str(tmp_path)
    )
    
    assert "evidence-only" in report
    assert "local candidate" in report
