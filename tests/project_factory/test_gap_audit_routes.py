from services.project_factory.gap_audit import GapAuditEngine


def test_gap_audit_checks_real_fastapi_routes(tmp_path):
    report = GapAuditEngine(str(tmp_path)).run_audit()

    assert report["missing_endpoints"] == []
    assert report["endpoints_audited"]["/api/v1/project-factory/{project_id}/apply-preview/run"] == "VERIFIED_PRESENT"
    assert report["endpoints_audited"]["/api/v1/project-factory/portfolio/policy-final/{proposal_id}/approve"] == "VERIFIED_PRESENT"
