"""Tests for Verifier Mesh Adapter."""
import pytest
from services.project_factory.verifier_mesh_adapter import run_verifier_mesh
from services.project_factory.models import VerifierMeshReport


def test_verifier_mesh_all_clean(monkeypatch, tmp_path):
    """All guards pass — overall PASSED."""
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_delivery_manifest", lambda p, r: {
        "production_apply_allowed": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False,
        "force_push_performed": False,
        "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.write_verifier_mesh_report", lambda p, d, r: None)

    result = run_verifier_mesh("PF-1", str(tmp_path))
    assert result.status == "PASSED"
    assert all(c.status == "PASSED" for c in result.checks)


def test_verifier_mesh_production_apply_allowed_fails(monkeypatch, tmp_path):
    """production_apply_allowed=true → FAILED."""
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_delivery_manifest", lambda p, r: {
        "production_apply_allowed": True,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False,
        "force_push_performed": False,
        "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.write_verifier_mesh_report", lambda p, d, r: None)

    result = run_verifier_mesh("PF-1", str(tmp_path))
    assert result.status == "FAILED"
    failed = [c for c in result.checks if c.status == "FAILED"]
    assert any("production_apply_guard" in c.name for c in failed)


def test_verifier_mesh_merge_guard_fails(monkeypatch, tmp_path):
    """merge_performed=true → merge_guard FAILED."""
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_delivery_manifest", lambda p, r: {
        "production_apply_allowed": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_draft_pr_creation", lambda p, r: {
        "merge_performed": True,
        "force_push_performed": False,
        "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.write_verifier_mesh_report", lambda p, d, r: None)

    result = run_verifier_mesh("PF-1", str(tmp_path))
    assert result.status == "FAILED"
    failed = [c for c in result.checks if c.status == "FAILED"]
    assert any("merge_guard" in c.name for c in failed)


def test_verifier_mesh_force_push_guard_fails(monkeypatch, tmp_path):
    """force_push_performed=true → force_push_guard FAILED."""
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_delivery_manifest", lambda p, r: {
        "production_apply_allowed": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False,
        "force_push_performed": True,
        "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.write_verifier_mesh_report", lambda p, d, r: None)

    result = run_verifier_mesh("PF-1", str(tmp_path))
    assert result.status == "FAILED"
    failed = [c for c in result.checks if c.status == "FAILED"]
    assert any("force_push_guard" in c.name for c in failed)


def test_verifier_mesh_production_write_guard_fails(monkeypatch, tmp_path):
    """production_direct_write=true → production_write_guard FAILED."""
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_delivery_manifest", lambda p, r: {
        "production_apply_allowed": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False,
        "force_push_performed": False,
        "production_direct_write": True,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.write_verifier_mesh_report", lambda p, d, r: None)

    result = run_verifier_mesh("PF-1", str(tmp_path))
    assert result.status == "FAILED"
    failed = [c for c in result.checks if c.status == "FAILED"]
    assert any("production_write_guard" in c.name for c in failed)


def test_verifier_mesh_no_artifacts_skips(monkeypatch, tmp_path):
    """Missing artifacts → SKIPPED checks, overall PASSED."""
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_delivery_manifest", lambda p, r: None)
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_draft_pr_creation", lambda p, r: None)
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.write_verifier_mesh_report", lambda p, d, r: None)

    result = run_verifier_mesh("PF-1", str(tmp_path))
    assert result.status == "PASSED"
    assert all(c.status in ("SKIPPED", "PASSED") for c in result.checks)


def test_verifier_mesh_with_test_flag(monkeypatch, tmp_path):
    """run_tests=True adds SKIPPED test check entries."""
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_delivery_manifest", lambda p, r: {
        "production_apply_allowed": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.load_draft_pr_creation", lambda p, r: {
        "merge_performed": False, "force_push_performed": False, "production_direct_write": False,
    })
    monkeypatch.setattr("services.project_factory.verifier_mesh_adapter.write_verifier_mesh_report", lambda p, d, r: None)

    result = run_verifier_mesh("PF-1", str(tmp_path), run_tests=True)
    assert result.status == "PASSED"
    test_checks = [c for c in result.checks if c.name.startswith("tests_")]
    assert len(test_checks) == 2
    assert all(c.status == "SKIPPED" for c in test_checks)
