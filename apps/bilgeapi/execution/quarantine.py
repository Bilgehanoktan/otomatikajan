import shutil
from pathlib import Path
from typing import Optional


class QuarantineManager:
    """
    Quarantine Manager for BilgeAPI Execution.
    Quarantines suspicious or deleted files for review before permanent removal.
    """

    def __init__(self, project_root: Path, workspace_dir: Path):
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = Path(workspace_dir).resolve()
        self.quarantine_dir = self.workspace_dir / "quarantine"
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def quarantine_file(self, filepath: Path) -> Path:
        target = Path(filepath).resolve()
        if not target.exists():
            raise FileNotFoundError(f"File '{filepath}' does not exist for quarantine")

        dest = self.quarantine_dir / target.name
        shutil.move(target, dest)
        return dest
