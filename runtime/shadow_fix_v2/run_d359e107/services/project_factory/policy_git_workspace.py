import os
import subprocess
from typing import List, Dict, Any, Optional

class PolicyGitWorkspace:
    """
    Safe wrapper for executing git operations during Phase 18 PR creation.
    Enforces strict rules:
    - No merge, rebase, reset, tag, or force push
    - No `git add .` or `git add -A`
    - Branches must start with `codex/`
    - Only specified files can be added
    """
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        
    def _run(self, cmd: List[str]) -> str:
        # Safety interceptors
        cmd_str = " ".join(cmd).lower()
        if any(bad in cmd_str for bad in [" merge ", " rebase ", " reset ", " tag ", " --force", " -f "]):
            raise ValueError(f"Dangerous git operation blocked: {cmd_str}")
        if "add ." in cmd_str or "add -a" in cmd_str:
            raise ValueError(f"Wildcard git add blocked: {cmd_str}")
            
        result = subprocess.run(
            cmd,
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {cmd_str}\nError: {result.stderr}")
        return result.stdout.strip()

    def get_status(self) -> str:
        return self._run(["git", "status", "--porcelain"])
        
    def checkout_new_branch(self, branch_name: str) -> None:
        if not branch_name.startswith("codex/"):
            raise ValueError("Branch name must start with 'codex/'")
        self._run(["git", "checkout", "-b", branch_name])
        
    def add_files(self, files: List[str]) -> None:
        if not files:
            return
        # Ensure files are passed explicitly
        cmd = ["git", "add"] + files
        self._run(cmd)
        
    def commit(self, message: str) -> str:
        self._run(["git", "commit", "-m", message])
        # Return commit SHA
        return self._run(["git", "rev-parse", "HEAD"])
        
    def push_branch(self, remote: str, branch_name: str) -> None:
        if not branch_name.startswith("codex/"):
            raise ValueError("Can only push codex/ branches")
        self._run(["git", "push", "-u", remote, branch_name])
