"""Tests for PR-Agent static review adapter."""
import pytest
from services.project_factory.pr_agent_review import run_pr_agent_review
from services.project_factory.models import PrAgentReview


def test_pr_agent_review_clean_pass(monkeypatch, tmp_path):
    """All clean — no findings."""
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False,
        "force_push_performed": False,
        "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_apply_preview", lambda p, r: {
        "blocking_risks": [],
    })
    monkeypatch.setattr("services.project_factory.pr_agent_review._load_json_artifact", lambda p, n, r: None)
    monkeypatch.setattr("services.project_factory.pr_agent_review._resolve_project_dir", lambda p, r: tmp_path)
    monkeypatch.setattr("services.project_factory.pr_agent_review.write_pr_agent_review", lambda p, d, r: None)

    result = run_pr_agent_review("PF-1", str(tmp_path))
    assert result.status == "PASSED"
    assert len(result.findings) == 0


def test_pr_agent_review_merge_performed_blocks(monkeypatch, tmp_path):
    """merge_performed=true produces a blocking finding."""
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_draft_pr_creation", lambda p, r: {
        "merge_performed": True,
        "force_push_performed": False,
        "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_apply_preview", lambda p, r: {"blocking_risks": []})
    monkeypatch.setattr("services.project_factory.pr_agent_review._load_json_artifact", lambda p, n, r: None)
    monkeypatch.setattr("services.project_factory.pr_agent_review._resolve_project_dir", lambda p, r: tmp_path)
    monkeypatch.setattr("services.project_factory.pr_agent_review.write_pr_agent_review", lambda p, d, r: None)

    result = run_pr_agent_review("PF-1", str(tmp_path))
    assert result.status == "BLOCKED"
    blocking = [f for f in result.findings if f.severity == "blocking"]
    assert any("merge_performed" in f.description for f in blocking)


def test_pr_agent_review_force_push_blocks(monkeypatch, tmp_path):
    """force_push_performed=true produces a blocking finding."""
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False,
        "force_push_performed": True,
        "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_apply_preview", lambda p, r: {"blocking_risks": []})
    monkeypatch.setattr("services.project_factory.pr_agent_review._load_json_artifact", lambda p, n, r: None)
    monkeypatch.setattr("services.project_factory.pr_agent_review._resolve_project_dir", lambda p, r: tmp_path)
    monkeypatch.setattr("services.project_factory.pr_agent_review.write_pr_agent_review", lambda p, d, r: None)

    result = run_pr_agent_review("PF-1", str(tmp_path))
    assert result.status == "BLOCKED"
    blocking = [f for f in result.findings if f.severity == "blocking"]
    assert any("force_push" in f.description for f in blocking)


def test_pr_agent_review_production_direct_write_blocks(monkeypatch, tmp_path):
    """production_direct_write=true produces a blocking finding."""
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False,
        "force_push_performed": False,
        "production_direct_write": True,
    })
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_apply_preview", lambda p, r: {"blocking_risks": []})
    monkeypatch.setattr("services.project_factory.pr_agent_review._load_json_artifact", lambda p, n, r: None)
    monkeypatch.setattr("services.project_factory.pr_agent_review._resolve_project_dir", lambda p, r: tmp_path)
    monkeypatch.setattr("services.project_factory.pr_agent_review.write_pr_agent_review", lambda p, d, r: None)

    result = run_pr_agent_review("PF-1", str(tmp_path))
    assert result.status == "BLOCKED"
    blocking = [f for f in result.findings if f.severity == "blocking"]
    assert any("production_direct_write" in f.description for f in blocking)


def test_pr_agent_review_risky_file_detected(monkeypatch, tmp_path):
    """Risky file extension (.env) produces blocking finding."""
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False, "force_push_performed": False, "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_apply_preview", lambda p, r: {"blocking_risks": []})

    def mock_load_artifact(p, name, r):
        if name == "candidate_manifest.json":
            return {"files": [{"path": "config/.env"}]}
        return None

    monkeypatch.setattr("services.project_factory.pr_agent_review._load_json_artifact", mock_load_artifact)
    monkeypatch.setattr("services.project_factory.pr_agent_review._resolve_project_dir", lambda p, r: tmp_path)
    monkeypatch.setattr("services.project_factory.pr_agent_review.write_pr_agent_review", lambda p, d, r: None)

    result = run_pr_agent_review("PF-1", str(tmp_path))
    assert result.status == "BLOCKED"
    assert any("Risky file" in f.description for f in result.findings)


def test_pr_agent_review_no_draft_pr_still_works(monkeypatch, tmp_path):
    """Fallback: no draft_pr_creation available — review still runs."""
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_draft_pr_creation", lambda p, r: None)
    monkeypatch.setattr("services.project_factory.pr_agent_review.load_apply_preview", lambda p, r: None)
    monkeypatch.setattr("services.project_factory.pr_agent_review._load_json_artifact", lambda p, n, r: None)
    monkeypatch.setattr("services.project_factory.pr_agent_review._resolve_project_dir", lambda p, r: tmp_path)
    monkeypatch.setattr("services.project_factory.pr_agent_review.write_pr_agent_review", lambda p, d, r: None)

    result = run_pr_agent_review("PF-1", str(tmp_path))
    assert result.status == "PASSED"
