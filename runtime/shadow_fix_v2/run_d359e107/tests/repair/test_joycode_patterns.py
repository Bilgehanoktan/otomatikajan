from services.repair.joycode_patterns import evaluate_fail2pass_pass2pass
from services.repair.repair_models import RepairCandidate, RepairCase, SandboxResult


def test_empty_patch_recommends_retry(tmp_path):
    patch_path = tmp_path / "patch.diff"
    patch_path.write_text("", encoding="utf-8")
    result = evaluate_fail2pass_pass2pass(
        RepairCase(incident_id="INC-JOY", failed_command="pytest tests/repair"),
        RepairCandidate(candidate_id="C-JOY", patch_path=str(patch_path), changed_files=[]),
        SandboxResult(patch_applied=True, tests_passed=True),
    )

    assert result["failure_attribution"] == "empty_patch"
    assert result["retry_recommended"] is True


def test_test_only_patch_is_marked_as_suppression_risk(tmp_path):
    patch_path = tmp_path / "patch.diff"
    patch_path.write_text("--- a/tests/x.py\n+++ b/tests/x.py\n", encoding="utf-8")
    result = evaluate_fail2pass_pass2pass(
        RepairCase(incident_id="INC-JOY-2", failed_command="pytest tests/repair"),
        RepairCandidate(candidate_id="C-JOY-2", patch_path=str(patch_path), changed_files=["tests/x.py"]),
        SandboxResult(patch_applied=True, tests_passed=True),
    )

    assert result["failure_attribution"] == "test_suppression_risk"
    assert result["patch_only_tests"] is True

