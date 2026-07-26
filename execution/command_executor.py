import os
import sys
import time
import shlex
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from bilgeapi.governance.policy_engine import PolicyEngine

logger = logging.getLogger("bilgeapi.execution.command_executor")


class SafeCommandExecutor:
    """
    Validates and executes shell commands securely using PolicyEngine and allow/deny rules.
    Prevents command injection by parsing arguments via shlex and executing with shell=False.
    """

    ALLOWLIST: List[str] = [
        "git diff",
        "pytest",
        "npm run test",
        "npm test",
        "python -m pytest",
        "python -m unittest",
        "go test",
        "cargo test",
    ]

    DENYLIST: List[str] = [
        "sudo", "ssh", "wget", "curl", "chmod", "chown", "mv", "cp", "dd",
        ";", "&", "|", "`", "$("
    ]

    def __init__(self, project_root: Path, workspace_dir: Path, policy_engine: PolicyEngine):
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = Path(workspace_dir).resolve()
        self.policy_engine = policy_engine

    def execute_command(
        self,
        command: str,
        approved: bool = False,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Validates the command string and executes it securely inside the project root.
        
        Args:
            command: The command string to execute.
            approved: Whether the action has received explicit human approval.
            env: Optional environment variables for the subprocess.
            
        Returns:
            Dict containing exit_code, stdout, stderr, and execution status.
        """
        cmd_clean = command.strip()
        if not cmd_clean:
            raise ValueError("Command string cannot be empty")

        # 1. Defense-in-depth: Reject hardcoded denylist patterns (checked first)
        cmd_lower = cmd_clean.lower()
        
        # Explicit check for "rm " (with space) or "rm -rf"
        if "rm " in cmd_lower or "rm-" in cmd_lower:
            raise ValueError(f"Command '{cmd_clean}' contains forbidden keyword: rm")
            
        for term in self.DENYLIST:
            if term in cmd_lower:
                raise ValueError(f"Command '{cmd_clean}' contains forbidden token/character: {term}")

        # 2. ALLOWLIST Validation: Must raise PermissionError if not allowed
        allowed = False
        for pattern in self.ALLOWLIST:
            if cmd_clean.startswith(pattern):
                allowed = True
                break
        if not allowed:
            raise PermissionError(f"Command '{cmd_clean}' is not in the ALLOWLIST of safe commands (requires human approval)")

        # 3. Check general policy configuration
        decision_dict = self.policy_engine.decide_command_action(cmd_clean)
        decision = decision_dict["decision"]
        risk_level = decision_dict["risk_level"]

        if decision == "DENY" or risk_level == "CRITICAL":
            raise ValueError(f"Command '{cmd_clean}' is DENIED by policy")
        if (decision == "APPROVAL_REQUIRED" or risk_level == "HIGH") and not approved:
            raise PermissionError(f"Command '{cmd_clean}' requires human approval")

        # 4. Secure parsing and execution
        try:
            cmd_args = shlex.split(cmd_clean)
        except ValueError as e:
            raise ValueError(f"Failed to parse command string: {e}")

        if not cmd_args:
            raise ValueError("Command parsed to empty argument list")

        # Environment variables isolation: Only pass safe environment variables
        process_env = {}
        allowed_env_keys = {"PATH", "TEMP", "TMP", "SYSTEMROOT", "COMSPEC", "PYTHONPATH", "LANG", "LC_ALL", "USER", "HOME"}
        for k, v in os.environ.items():
            if k in allowed_env_keys:
                process_env[k] = v
        if env:
            process_env.update(env)

        try:
            # Run command securely (shell=False) with a 30s timeout
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                env=process_env,
                check=False,
                timeout=30
            )
            
            # Limit stdout/stderr sizes
            max_len = 10 * 1024 * 1024  # 10 MB limit
            stdout_str = result.stdout
            if stdout_str and len(stdout_str.encode('utf-8')) > max_len:
                stdout_str = stdout_str[:max_len] + "\n[Output Truncated: Exceeded 10MB]"
                
            stderr_str = result.stderr
            if stderr_str and len(stderr_str.encode('utf-8')) > max_len:
                stderr_str = stderr_str[:max_len] + "\n[Output Truncated: Exceeded 10MB]"

            return {
                "status": "SUCCESS" if result.returncode == 0 else "FAILED",
                "exit_code": result.returncode,
                "stdout": stdout_str,
                "stderr": stderr_str
            }
        except subprocess.TimeoutExpired as e:
            # Kill process tree on timeout
            if sys.platform == "win32":
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(e.pid)], capture_output=True, check=False)
                except Exception:
                    pass
            else:
                try:
                    import os as _os
                    import signal as _signal
                    _os.killpg(_os.getpgid(e.pid), _signal.SIGKILL)
                except Exception:
                    pass
            raise
        except FileNotFoundError:
            raise FileNotFoundError(f"Executable not found for command: {cmd_args[0]}")
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "status": "FAILED",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
