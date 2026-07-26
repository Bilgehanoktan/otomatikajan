import difflib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from bilgeapi.governance.policy_engine import PolicyEngine
from bilgeapi.execution.rollback_manager import RollbackManager
from bilgeapi.execution.quarantine import QuarantineManager


class PathGuard:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def validate_and_resolve(self, filepath: str) -> Path:
        resolved = (self.project_root / filepath).resolve()
        if not str(resolved).startswith(str(self.project_root)):
            raise PermissionError(f"Path '{filepath}' escapes project root boundary")
        return resolved


class FileExecutor:
    """
    Executes file modifications (write, edit, delete, patch, rename) under PolicyEngine control.
    Supports dry-run verification mode.
    """

    def __init__(
        self,
        project_root: Path,
        workspace_dir: Path,
        policy_engine: PolicyEngine,
        rollback_manager: Optional[RollbackManager] = None,
        quarantine_manager: Optional[QuarantineManager] = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = Path(workspace_dir).resolve()
        self.policy_engine = policy_engine
        self.rollback_manager = rollback_manager or RollbackManager(project_root, workspace_dir)
        self.quarantine_manager = quarantine_manager or QuarantineManager(project_root, workspace_dir)
        self.path_guard = PathGuard(self.project_root)
        self.dry_run = False
        self.dry_run_files: set[str] = set()
        self._pending_dry_run_ops: List[Dict[str, Any]] = []

    def set_dry_run(self, enabled: bool):
        self.dry_run = enabled
        if not enabled:
            self.dry_run_files.clear()
            self._pending_dry_run_ops.clear()

    def apply_dry_run_changes(self, approved: bool = False) -> List[Dict[str, Any]]:
        results = []
        old_dry_run = self.dry_run
        self.dry_run = False
        try:
            for op in self._pending_dry_run_ops:
                action = op.get("action")
                filepath = op.get("filepath")
                if action == "write":
                    res = self.write_file(filepath, op["content"], approved=approved)
                    results.append({"status": "SUCCESS", "action": "WRITE", "filepath": str(filepath)})
                elif action == "patch":
                    res = self.patch_file(filepath, op["original_snippet"], op["replacement_snippet"], approved=approved)
                    results.append({"status": "SUCCESS", "action": "PATCH", "filepath": str(filepath)})
                elif action == "rename":
                    res = self.rename_file(filepath, op["new_filepath"], approved=approved)
                    results.append({"status": "SUCCESS", "action": "RENAME", "filepath": str(filepath)})
                elif action == "delete":
                    res = self.delete_file(filepath, approved=approved)
                    results.append({"status": "SUCCESS", "action": "DELETE", "filepath": str(filepath)})
        finally:
            self.dry_run = old_dry_run
            self.dry_run_files.clear()
            self._pending_dry_run_ops.clear()

        return results

    def write_file(self, filepath: str, content: str, approved: bool = False) -> Dict[str, Any]:
        target = self.path_guard.validate_and_resolve(filepath)
        decision = self.policy_engine.decide_file_action("Write", filepath)

        if decision["decision"] == "DENY":
            raise ValueError(f"Write operation on '{filepath}' DENIED: {decision['reason']}")
        if decision["decision"] == "APPROVAL_REQUIRED" and not approved:
            raise PermissionError(f"Write operation on '{filepath}' requires human approval")

        old_content = target.read_text(encoding="utf-8") if target.exists() else ""
        diff = "".join(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}"
        )) or f"+ {content}"

        if self.dry_run:
            self.dry_run_files.add(filepath)
            self._pending_dry_run_ops.append({"action": "write", "filepath": filepath, "content": content})
            return {
                "status": "SUCCESS",
                "action": "WRITE_DRY_RUN",
                "diff": diff,
                "filepath": str(target)
            }

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"status": "SUCCESS", "filepath": str(target), "diff": diff}

    def patch_file(
        self, filepath: str, original_snippet: str, replacement_snippet: str, approved: bool = False
    ) -> Dict[str, Any]:
        target = self.path_guard.validate_and_resolve(filepath)
        decision = self.policy_engine.decide_file_action("Edit", filepath)

        if decision["decision"] == "DENY":
            raise ValueError(f"Patch operation on '{filepath}' DENIED: {decision['reason']}")
        if decision["decision"] == "APPROVAL_REQUIRED" and not approved:
            raise PermissionError(f"Patch operation on '{filepath}' requires human approval")

        if not target.exists():
            raise FileNotFoundError(f"Target file '{filepath}' does not exist for patching")

        old_content = target.read_text(encoding="utf-8")
        if original_snippet not in old_content:
            raise ValueError(f"Snippet not found in '{filepath}'")

        new_content = old_content.replace(original_snippet, replacement_snippet, 1)
        diff = "".join(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}"
        )) or f"- {original_snippet}\n+ {replacement_snippet}"

        if self.dry_run:
            self.dry_run_files.add(filepath)
            self._pending_dry_run_ops.append({
                "action": "patch",
                "filepath": filepath,
                "original_snippet": original_snippet,
                "replacement_snippet": replacement_snippet
            })
            return {
                "status": "SUCCESS",
                "action": "PATCH_DRY_RUN",
                "diff": diff,
                "filepath": str(target)
            }

        target.write_text(new_content, encoding="utf-8")
        return {"status": "SUCCESS", "filepath": str(target), "diff": diff}

    def rename_file(self, filepath: str, new_filepath: str, approved: bool = False) -> Dict[str, Any]:
        target = self.path_guard.validate_and_resolve(filepath)
        new_target = self.path_guard.validate_and_resolve(new_filepath)
        decision = self.policy_engine.decide_file_action("Rename", filepath)

        if decision["decision"] == "DENY":
            raise ValueError(f"Rename operation on '{filepath}' DENIED: {decision['reason']}")
        if decision["decision"] == "APPROVAL_REQUIRED" and not approved:
            raise PermissionError(f"Rename operation on '{filepath}' requires human approval")

        if self.dry_run:
            self.dry_run_files.add(filepath)
            self._pending_dry_run_ops.append({"action": "rename", "filepath": filepath, "new_filepath": new_filepath})
            return {
                "status": "SUCCESS",
                "action": "RENAME_DRY_RUN",
                "filepath": str(target),
                "new_filepath": str(new_target)
            }

        if target.exists():
            new_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(target, new_target)

        return {"status": "SUCCESS", "filepath": str(target), "new_filepath": str(new_target)}

    def delete_file(self, filepath: str, approved: bool = False) -> Dict[str, Any]:
        target = self.path_guard.validate_and_resolve(filepath)
        decision = self.policy_engine.decide_file_action("Delete", filepath)

        if decision["decision"] == "DENY":
            raise ValueError(f"Delete operation on '{filepath}' DENIED: {decision['reason']}")
        if decision["decision"] == "APPROVAL_REQUIRED" and not approved:
            raise PermissionError(f"Delete operation on '{filepath}' requires human approval")

        if self.dry_run:
            self.dry_run_files.add(filepath)
            self._pending_dry_run_ops.append({"action": "delete", "filepath": filepath})
            return {
                "status": "SUCCESS",
                "action": "DELETE_DRY_RUN",
                "filepath": str(target)
            }

        if target.exists():
            self.quarantine_manager.quarantine_file(target)

        return {"status": "SUCCESS", "filepath": str(target)}
