import os
import shutil
from pathlib import Path
from typing import Optional


class RollbackManager:
    """
    Rollback Manager for BilgeAPI Execution.
    Creates file backups before modification and restores them if verification fails.
    """

    def __init__(self, project_root: Path, workspace_dir: Path):
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = Path(workspace_dir).resolve()
        self.snapshots_dir = self.workspace_dir / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, filepath: Path) -> Optional[Path]:
        return self.create_backup(str(filepath))

    def create_backup(self, filepath: str) -> Optional[Path]:
        target = (self.project_root / filepath).resolve() if not Path(filepath).is_absolute() else Path(filepath).resolve()
        if not target.exists():
            return None

        rel_path = target.name
        snapshot_path = self.snapshots_dir / f"{rel_path}.bak"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, snapshot_path)
        return snapshot_path

    def restore_backup(self, filepath: str, backup_path: Optional[Path]):
        target = (self.project_root / filepath).resolve() if not Path(filepath).is_absolute() else Path(filepath).resolve()
        if backup_path and Path(backup_path).exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, target)
        elif target.exists():
            target.unlink()

    def remove_backup(self, backup_path: Optional[Path]):
        if backup_path and Path(backup_path).exists():
            try:
                Path(backup_path).unlink()
            except OSError:
                pass

    def rollback(self, snapshot_path: Optional[Path], target_filepath: Path):
        self.restore_backup(str(target_filepath), snapshot_path)

    def clean_snapshot(self, snapshot_path: Optional[Path]):
        self.remove_backup(snapshot_path)
