import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Optional
from services.project_factory.artifacts import _resolve_project_dir

class GitSafetyViolation(Exception):
    pass

class GitWorkspaceExecutor:
    """
    A controlled wrapper around git operations ensuring no merges, 
    no force pushes, and no direct commits to main/master.
    """
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    def _run_cmd(self, cmd: List[str]) -> str:
        """Runs a command and returns stripped stdout."""
        # Hard-blocked commands
        forbidden_terms = ["merge", "rebase", "reset", "clean", "tag", "--force", "-f", "add .", "add -A"]
        cmd_str = " ".join(cmd)
        
        for term in forbidden_terms:
            if f" {term}" in cmd_str or cmd_str.endswith(term):
                raise GitSafetyViolation(f"Forbidden git operation detected: {term} in command '{cmd_str}'")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() or e.stdout.strip()
            raise RuntimeError(f"Git command failed: {' '.join(cmd)}\nError: {err_msg}")

    def get_status(self) -> str:
        return self._run_cmd(["git", "status", "--porcelain"])

    def create_and_checkout_branch(self, branch_name: str) -> None:
        if not branch_name.startswith("codex/"):
            raise GitSafetyViolation(f"Branch name must start with 'codex/'. Found: {branch_name}")
        self._run_cmd(["git", "checkout", "-b", branch_name])

    def apply_delivery_files(self, project_id: str, files_to_apply: List[str]) -> None:
        """
        Copies delivery files to the workspace root securely, then `git add`s each file individually.
        """
        project_dir = _resolve_project_dir(project_id, str(self.workspace_root))
        delivery_files_dir = project_dir / "delivery_package" / "files"
        
        for file_path in files_to_apply:
            src = (delivery_files_dir / file_path).resolve()
            dest = (self.workspace_root / file_path).resolve()
            try:
                src.relative_to(delivery_files_dir.resolve())
            except ValueError:
                raise GitSafetyViolation(f"Path traversal detected in delivery source: {file_path}")
            
            if not src.exists() or not src.is_file():
                continue # If not a file in delivery package, maybe it's meant to be deleted? We only support add/modify currently.
                
            # Path traversal safety
            try:
                dest.relative_to(self.workspace_root)
            except ValueError:
                raise GitSafetyViolation(f"Path traversal detected in file: {file_path}")
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            
            # Add file specifically
            self._run_cmd(["git", "add", file_path])

    def commit_changes(self, commit_message: str) -> str:
        self._run_cmd(["git", "commit", "-m", commit_message])
        # Return commit SHA
        return self._run_cmd(["git", "rev-parse", "HEAD"])

    def push_branch(self, remote: str, branch_name: str) -> None:
        if not branch_name.startswith("codex/"):
             raise GitSafetyViolation("Can only push codex/ prefixed branches.")
        self._run_cmd(["git", "push", "-u", remote, branch_name])
