from __future__ import annotations

from services.repair.joycode_patterns import evaluate_fail2pass_pass2pass
from services.repair.path_policy import is_forbidden_path
from services.repair.repair_models import RepairCandidate, RepairCase, SandboxResult


SENSITIVE_MARKERS = [
    "migrations/",
    "services/auth/",
    "governance",
    "constitutional_guard.py",
    "libs/config.py",
]


def run_verifier_mesh(
    repair_case: RepairCase,
    candidate: RepairCandidate,
    sandbox_result: SandboxResult,
) -> dict:
    forbidden_changed = [
        path for path in candidate.changed_files if is_forbidden_path(path, repair_case.forbidden_paths)
    ]
    sensitive_changed = [
        path for path in candidate.changed_files if any(marker in path.replace("\\", "/") for marker in SENSITIVE_MARKERS)
    ]
    targeted_test_passed = bool(sandbox_result.tests_passed)
    joycode_checks = evaluate_fail2pass_pass2pass(repair_case, candidate, sandbox_result)

    checks = {
        "targeted_test": targeted_test_passed,
        "regression_risk": not bool(sandbox_result.failed_commands),
        "lint_build": None,
        "forbidden_file_changed": not forbidden_changed,
        "sensitive_file_changed": not sensitive_changed,
        "patch_non_empty": joycode_checks["patch_non_empty"],
        "patch_only_tests": not joycode_checks["patch_only_tests"],
        "fail2pass": joycode_checks["fail2pass"],
        "pass2pass": joycode_checks["pass2pass"],
    }

    passed = (
        targeted_test_passed
        and not forbidden_changed
        and not sensitive_changed
        and joycode_checks["patch_non_empty"]
        and not joycode_checks["patch_only_tests"]
    )
    return {
        "status": "VERIFIER_PASSED" if passed else "VERIFIER_FAILED",
        "checks": checks,
        "forbidden_changed": forbidden_changed,
        "sensitive_changed": sensitive_changed,
        "joycode": joycode_checks,
        "notes": "Verifier Mesh adapter includes JoyCode-style Fail2Pass/Pass2Pass and failure attribution patterns.",
    }
