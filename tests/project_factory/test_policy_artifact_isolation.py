from services.project_factory.artifacts import (
    load_policy_pr_status,
    write_policy_pr_status,
    load_policy_apply_preview,
    write_policy_apply_preview,
)


def test_policy_status_artifacts_are_proposal_scoped(tmp_path):
    write_policy_pr_status("POL-A", {"proposal_id": "POL-A", "status": "A"}, str(tmp_path))
    write_policy_pr_status("POL-B", {"proposal_id": "POL-B", "status": "B"}, str(tmp_path))

    assert load_policy_pr_status("POL-A", str(tmp_path))["status"] == "A"
    assert load_policy_pr_status("POL-B", str(tmp_path))["status"] == "B"


def test_policy_apply_preview_artifacts_do_not_cross_read(tmp_path):
    write_policy_apply_preview("POL-A", {"proposal_id": "POL-A", "blocking_risks": []}, str(tmp_path))
    write_policy_apply_preview("POL-B", {"proposal_id": "POL-B", "blocking_risks": ["blocked"]}, str(tmp_path))

    assert load_policy_apply_preview("POL-A", str(tmp_path))["blocking_risks"] == []
    assert load_policy_apply_preview("POL-B", str(tmp_path))["blocking_risks"] == ["blocked"]
