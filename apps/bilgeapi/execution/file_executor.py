import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from apps.bilgeapi.security.path_guard import PathGuard
from apps.bilgeapi.security.secret_scanner import SecretScanner
from apps.bilgeapi.governance.policy_engine import PolicyEngine
from apps.bilgeapi.execution.rollback_manager import RollbackManager
from apps.bilgeapi.execution.quarantine import QuarantineManager

class FileExecutor:
    """
    The only authorized component in BilgeAPI to write, patch, rename, quarantine, 
    or modify files. Enforces PolicyEngine, PathGuard, RollbackManager, and SecretScanner.
    """
    def __init__(
        self,
        project_root: Path,
        workspace_dir: Path,
        policy_engine: PolicyEngine,
        rollback_manager: RollbackManager,
        quarantine_manager: QuarantineManager,
        secret_scanner: Optional[SecretScanner] = None
    ):
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = Path(workspace_dir).resolve()
        self.policy_engine = policy_engine
        self.rollback_manager = rollback_manager
        self.quarantine_manager = quarantine_manager
        self.secret_scanner = secret_scanner or SecretScanner()
        self.path_guard = PathGuard(self.project_root)

    def _enforce_policy(self, action: str, filepath: str, approved: bool = False) -> None:
        decision_dict = self.policy_engine.decide_file_action(action, filepath)
        decision = decision_dict["decision"]
        risk_level = decision_dict["risk_level"]

        if decision == "DENY" or risk_level == "CRITICAL":
            raise ValueError(f"Action '{action}' on path '{filepath}' is DENIED by policy")
        if (decision == "APPROVAL_REQUIRED" or risk_level == "HIGH") and not approved:
            raise PermissionError(f"Action '{action}' on path '{filepath}' requires human approval")

    def write_file(self, filepath: str, content: str, approved: bool = False) -> Dict[str, Any]:
        """
        Safely writes content to a file, applying policy checks, backup, and secret scanning.
        """
        # 1. Enforce path and policy rules
        target_path = self.path_guard.validate_and_resolve(filepath)
        self._enforce_policy("Write", filepath, approved=approved)

        # 2. Scan and mask secrets in content
        clean_content = self.secret_scanner.scan_and_mask(content)

        # 3. Create backup for rollback
        backup_path = self.rollback_manager.create_backup(filepath)

        # 4. Perform the write operation
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(clean_content)

        return {
            "status": "SUCCESS",
            "action": "WRITE",
            "filepath": filepath,
            "backup_path": backup_path
        }

    def patch_file(self, filepath: str, original_snippet: str, replacement_snippet: str, approved: bool = False) -> Dict[str, Any]:
        """
        Safely patches a file, replacing a specific snippet with a new one.
        """
        # 1. Enforce path and policy rules
        target_path = self.path_guard.validate_and_resolve(filepath)
        self._enforce_policy("Edit", filepath, approved=approved)

        if not target_path.exists():
            raise FileNotFoundError(f"File to patch not found: {filepath}")

        # Load current content
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        if original_snippet not in content:
            raise ValueError(f"Target snippet to replace not found in file: {filepath}")

        # 2. Scan and mask secrets in replacement snippet
        clean_replacement = self.secret_scanner.scan_and_mask(replacement_snippet)

        # 3. Create backup for rollback
        backup_path = self.rollback_manager.create_backup(filepath)

        # 4. Perform replace and write back
        new_content = content.replace(original_snippet, clean_replacement)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "status": "SUCCESS",
            "action": "PATCH",
            "filepath": filepath,
            "backup_path": backup_path
        }

    def rename_file(self, old_filepath: str, new_filepath: str, approved: bool = False) -> Dict[str, Any]:
        """
        Safely renames or moves a file.
        """
        # 1. Enforce path and policy rules on both old and new paths
        old_path = self.path_guard.validate_and_resolve(old_filepath)
        new_path = self.path_guard.validate_and_resolve(new_filepath)

        self._enforce_policy("Rename", old_filepath, approved=approved)
        self._enforce_policy("Write", new_filepath, approved=approved)

        if not old_path.exists():
            raise FileNotFoundError(f"Source file not found: {old_filepath}")

        # 2. Create backup for rollback (on the old file)
        backup_path = self.rollback_manager.create_backup(old_filepath)

        # 3. Perform rename
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(new_path))

        return {
            "status": "SUCCESS",
            "action": "RENAME",
            "old_filepath": old_filepath,
            "new_filepath": new_filepath,
            "backup_path": backup_path
        }

