from unittest.mock import patch

from services.project_factory.release_readiness import ReleaseReadinessOrchestrator


def test_release_readiness_requires_successful_smoke(tmp_path):
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    artifact_dir = tmp_path / "artifacts"
    fake_audit = {
        "status": "PASSED",
        "checked_modules": {},
        "missing_modules": [],
        "missing_endpoints": [],
        "endpoints_audited": {},
        "safety_audit": {},
        "ui_integration": {},
    }

    with patch("services.project_factory.release_readiness.GapAuditEngine.run_audit", return_value=fake_audit), \
         patch("services.project_factory.artifacts.write_policy_proposals", side_effect=RuntimeError("forced smoke failure")):
        result = ReleaseReadinessOrchestrator(
            str(workspace_root),
            str(artifact_dir),
        ).run_stabilization_pipeline()

    assert result["smoke"]["status"] == "WARNING"
    assert result["pack"]["ready_for_release"] is False
