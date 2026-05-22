from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

# Forbidden command substrings or symbols
FORBIDDEN_OPERATORS = [
    "&&", "||", ";", ">", ">>", "<", "|", "$(", "`", "start-process", "docker", "git", "curl", "wget", "env"
]

# Whitelist of allowed exact/starts-with commands
ALLOWED_COMMANDS = [
    "npm run build",
    "npm run lint",
    "npm test",
    "py -3.13 -m pytest",
    "py -3.13 -m compileall"
]

def check_command_safety(command_str: str) -> None:
    """
    Validates a command against strict security guidelines.
    Throws ValueError if unsafe.
    """
    normalized = command_str.strip().lower()

    # 1. Blacklist checks (forbidden substrings / symbols)
    for operator in FORBIDDEN_OPERATORS:
        if operator in normalized:
            raise ValueError(f"Unsafe operator/command '{operator}' detected in command: {command_str}")

    # 2. Whitelist checks
    is_whitelisted = False
    for allowed in ALLOWED_COMMANDS:
        if normalized == allowed.lower() or normalized.startswith(allowed.lower() + " "):
            is_whitelisted = True
            break

    if not is_whitelisted:
        raise ValueError(f"Command '{command_str}' is not in the approved whitelist of commands.")

def execute_sandbox_command(
    project_id: str,
    command_str: str,
    sandbox_path: Path,
) -> Dict[str, Any]:
    """
    Executes a whitelisted command strictly within the sandbox path.
    """
    # Verify command safety
    check_command_safety(command_str)

    # Ensure sandbox path is resolved and exists
    sandbox_path = Path(sandbox_path).resolve()
    if not sandbox_path.exists():
        raise FileNotFoundError(f"Sandbox directory does not exist: {sandbox_path}")

    # Execute whitelisted command securely
    try:
        # Run command with a timeout to prevent hanging
        res = subprocess.run(
            command_str,
            cwd=sandbox_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "status": "success",
            "command": command_str,
            "returncode": res.returncode,
            "stdout": res.stdout or "",
            "stderr": res.stderr or ""
        }
    except subprocess.TimeoutExpired as te:
        return {
            "status": "failed",
            "command": command_str,
            "returncode": -1,
            "stdout": te.stdout or "",
            "stderr": te.stderr or "Command execution timed out."
        }
    except Exception as e:
        return {
            "status": "failed",
            "command": command_str,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Subprocess error: {e}"
        }
