import shutil
import os
from typing import Optional
from pathlib import Path
from apps.bilgeapi.security.path_guard import PathGuard

class RollbackManager:
    def __init__(self, project_root: Path, workspace_dir: Path):
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = Path(workspace_dir).resolve()
        self.backup_dir = self.workspace_dir / "quarantine"  # Reusing quarantine folder for backups
        self.path_guard = PathGuard(self.project_root)
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, filepath: str) -> Optional[str]:
        """
        Creates a temporary backup copy of a file before modification.
        
        Args:
            filepath: Target file relative path.
            
        Returns:
            Optional[str]: Relative path of the backup file, or None if the file didn't exist.
        """
        target_path = self.path_guard.validate_and_resolve(filepath)
        if not target_path.exists():
            return None

        # Create unique backup name
        import uuid
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        backup_filename = f"bak_{timestamp}_{unique_id}_{target_path.name}"
        dest_path = self.backup_dir / backup_filename

        # Copy original file to backup destination
        shutil.copy2(str(target_path), str(dest_path))
        
        return str(dest_path.relative_to(self.project_root))

    def restore_backup(self, filepath: str, backup_path_str: str) -> None:
        """
        Restores a file from its backup copy.
        """
        target_path = self.path_guard.validate_and_resolve(filepath)
        backup_path = self.path_guard.validate_and_resolve(backup_path_str, allow_internal=True)

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path_str}")

        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy backup back to original location
        shutil.copy2(str(backup_path), str(target_path))

    def remove_backup(self, backup_path_str: str) -> None:
        """
        Removes the backup file once the change is verified as safe.
        """
        backup_path = self.path_guard.validate_and_resolve(backup_path_str, allow_internal=True)
        if backup_path.exists():
            os.remove(backup_path)
