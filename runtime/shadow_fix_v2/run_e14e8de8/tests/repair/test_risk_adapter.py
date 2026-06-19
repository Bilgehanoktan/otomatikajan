from services.repair.repair_models import RepairCandidate, RepairCase
from services.repair.risk_adapter import calculate_risk


def test_forbidden_path_change_blocks_auto_repair():
    case = RepairCase(incident_id="INC-RISK", forbidden_paths=["services/auth/"])
    candidate = RepairCandidate(
        candidate_id="C-1",
        patch_path="repair_outputs/INC-RISK/patch.diff",
        changed_files=["services/auth/router.py"],
    )

    decision = calculate_risk(case, candidate, {"status": "VERIFIER_PASSED"})

    assert decision.status == "AUTO_REPAIR_BLOCKED"
    assert decision.risk_score > 0.8
    assert decision.recommended_action == "Manual senior review required"


def test_low_risk_test_file_allows_draft_pr():
    case = RepairCase(incident_id="INC-LOW", forbidden_paths=["services/auth/"])
    candidate = RepairCandidate(
        candidate_id="C-2",
        patch_path="repair_outputs/INC-LOW/patch.diff",
        changed_files=["tests/repair/test_repair_orchestrator.py"],
    )

    decision = calculate_risk(case, candidate, {"status": "VERIFIER_PASSED"})

    assert decision.status == "DRAFT_PR_READY"
    assert decision.recommended_action == "DRAFT_PR_ALLOWED"
    assert decision.risk_level == "LOW"


def test_test_only_patch_is_blocked_by_joycode_attribution():
    case = RepairCase(incident_id="INC-TEST-ONLY", forbidden_paths=["services/auth/"])
    candidate = RepairCandidate(
        candidate_id="C-TEST-ONLY",
        patch_path="repair_outputs/INC-TEST-ONLY/patch.diff",
        changed_files=["tests/repair/test_fake.py"],
    )

    decision = calculate_risk(
        case,
        candidate,
        {
            "status": "VERIFIER_FAILED",
            "joycode": {"failure_attribution": "test_suppression_risk"},
        },
    )

    assert decision.status == "AUTO_REPAIR_BLOCKED"
    assert decision.risk_score > 0.8
