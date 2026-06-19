from __future__ import annotations

import shlex
from pathlib import Path


ALLOWED_EXECUTABLES = {
    "pytest",
    "pytest.exe",
    "py",
    "py.exe",
    "python",
    "python.exe",
    "npm",
    "npm.cmd",
    "git",
    "rg",
    "rg.exe",
    "grep",
    "cat",
    "sed",
}

FORBIDDEN_TOKENS = {
    "sudo",
    "printenv",
    "env",
    "chmod",
    "wget",
}

FORBIDDEN_EXACT_PREFIXES = {
    "git push origin main",
    "git reset --hard main",
    "cat .env",
    "docker system prune",
    "rm -rf /",
}

CONTROL_OPERATORS = ["&&", "||", "|", ";", ">", "<", "`"]


def command_args(command: str) -> list[str]:
    if any(operator in command for operator in CONTROL_OPERATORS):
        raise ValueError("failed_command contains unsupported shell control operators")
    args = shlex.split(command, posix=False)
    if not args:
        raise ValueError("failed_command is empty")
    return args


def validate_command(command: str) -> list[str]:
    lowered = " ".join(command.strip().lower().split())
    for prefix in FORBIDDEN_EXACT_PREFIXES:
        if lowered.startswith(prefix):
            raise ValueError(f"failed_command is forbidden: {prefix}")

    args = command_args(command)
    executable = Path(args[0]).name.lower()
    if executable not in ALLOWED_EXECUTABLES:
        raise ValueError(f"failed_command executable is not allowed: {args[0]}")
    if executable in FORBIDDEN_TOKENS:
        raise ValueError(f"failed_command executable is forbidden: {args[0]}")
    if any(str(arg).lower() == ".env" or str(arg).lower().endswith("/.env") for arg in args[1:]):
        raise ValueError("failed_command cannot read .env")
    if executable == "git" and len(args) >= 2 and args[1].lower() not in {"diff", "status"}:
        raise ValueError("Only git diff and git status are allowed in repair sandbox commands")
    if executable in {"npm", "npm.cmd"}:
        normalized = " ".join(arg.lower() for arg in args[:3])
        allowed = normalized in {"npm test", "npm run build", "npm run lint"}
        if not allowed:
            raise ValueError("Only npm test, npm run build, and npm run lint are allowed")
    return args


def is_command_allowed(command: str) -> bool:
    try:
        validate_command(command)
        return True
    except ValueError:
        return False

