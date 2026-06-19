from services.repair.command_policy import is_command_allowed, validate_command


def test_allowed_commands():
    assert is_command_allowed("pytest tests/repair")
    assert is_command_allowed("npm run build")
    assert is_command_allowed("git diff")


def test_forbidden_commands():
    assert not is_command_allowed("git push origin main")
    assert not is_command_allowed("cat .env")
    assert not is_command_allowed("sudo pytest")


def test_shell_control_operator_is_rejected():
    try:
        validate_command("pytest tests && cat .env")
    except ValueError as exc:
        assert "unsupported shell control operators" in str(exc)
    else:
        raise AssertionError("validate_command should reject shell control operators")

