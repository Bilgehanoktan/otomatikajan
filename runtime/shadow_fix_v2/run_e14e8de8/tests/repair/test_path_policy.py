from services.repair.path_policy import evaluate_changed_paths, is_forbidden_path


def test_forbidden_paths_block_auto_repair():
    assert is_forbidden_path("services/auth/router.py", ["services/auth/"])
    assert is_forbidden_path("libs/config.py", ["libs/config.py"])


def test_low_risk_paths_are_allowed():
    result = evaluate_changed_paths(["tests/repair/test_path_policy.py", "docs/repair.md"], ["services/auth/"])

    assert result["allowed"] is True
    assert result["status"] == "PATHS_ALLOWED"

