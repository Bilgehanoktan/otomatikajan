from __future__ import annotations

from pathlib import Path

from services.repair.repair_models import RepairCandidate, RepairCase, SandboxResult


def _patch_text(candidate: RepairCandidate) -> str:
    path = Path(candidate.patch_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def patch_is_empty(candidate: RepairCandidate) -> bool:
    return not _patch_text(candidate).strip()


def patch_only_changes_tests(candidate: RepairCandidate) -> bool:
    changed = [path.replace("\\", "/") for path in candidate.changed_files]
    return bool(changed) and all(path.startswith("tests/") or "/tests/" in path for path in changed)


def evaluate_fail2pass_pass2pass(
    repair_case: RepairCase,
    candidate: RepairCandidate,
    sandbox_result: SandboxResult,
) -> dict:
    empty_patch = patch_is_empty(candidate)
    test_only = patch_only_changes_tests(candidate)
    fail2pass = bool(sandbox_result.tests_passed and repair_case.failed_command)
    pass2pass = bool(sandbox_result.tests_passed and not sandbox_result.failed_commands)
    if empty_patch:
        attribution = "empty_patch"
    elif not sandbox_result.tests_passed:
        attribution = "patch_failed_targeted_test"
    elif test_only:
        attribution = "test_suppression_risk"
    else:
        attribution = "patch_candidate_supported"

    return {
        "fail2pass": fail2pass,
        "pass2pass": pass2pass,
        "patch_non_empty": not empty_patch,
        "patch_only_tests": test_only,
        "failure_attribution": attribution,
        "retry_recommended": attribution in {"empty_patch", "patch_failed_targeted_test"},
    }

