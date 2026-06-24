import shutil
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from apps.bilgeapi.security.path_guard import PathGuard
from apps.bilgeapi.memory.repositories import QuarantineItemRepository

class QuarantineManager:
    def __init__(self, project_root: Path, workspace_dir: Path):
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = Path(workspace_dir).resolve()
        self.quarantine_dir = self.workspace_dir / "quarantine"
        self.path_guard = PathGuard(self.project_root)

        # Ensure quarantine directory exists
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def _calculate_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def quarantine_file(
        self,
        filepath: str,
        reason: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Moves a file to the .bilgeapi/quarantine directory and registers it in database.
        
        Returns:
            Dict[str, Any]: The database record of the quarantined item.
        """
        # 1. Resolve and validate target path
        target_path = self.path_guard.validate_and_resolve(filepath)
        
        if not target_path.exists():
            raise FileNotFoundError(f"Target file for quarantine does not exist: {filepath}")
        if not target_path.is_file():
            raise ValueError(f"Quarantine is only supported for files: {filepath}")

        # 2. Calculate original hash
        orig_hash = self._calculate_hash(target_path)

        # 3. Create destination file inside quarantine folder
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        quarantine_filename = f"q_{timestamp}_{unique_id}_{target_path.name}"
        dest_path = self.quarantine_dir / quarantine_filename

        # 4. Move file
        # We use shutil.move to relocate the file
        shutil.move(str(target_path), str(dest_path))

        # 5. Get relative path to original file and quarantine file
        rel_filepath = str(target_path.relative_to(self.project_root))
        rel_quarantine_path = str(dest_path.relative_to(self.project_root))

        # 6. Save in SQLite
        repo = QuarantineItemRepository(db_session)
        item = await repo.quarantine_file(
            filepath=rel_filepath,
            original_hash=orig_hash,
            quarantine_path=rel_quarantine_path,
            reason=reason
        )
        return item

    async def restore_file(
        self,
        item_id: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Restores a previously quarantined file to its original location.
        """
        repo = QuarantineItemRepository(db_session)
        from apps.bilgeapi.memory.models import QuarantineItemModel
        from sqlalchemy import select
        stmt = select(QuarantineItemModel).where(QuarantineItemModel.id == item_id)
        db_res = await db_session.execute(stmt)
        item_obj = db_res.scalar_one_or_none()
        
        if not item_obj:
            raise FileNotFoundError(f"Quarantine record not found for id: {item_id}")
        if item_obj.restored:
            raise ValueError(f"Quarantine item {item_id} is already restored")

        # Resolve paths
        orig_path = self.project_root / item_obj.filepath
        quar_path = self.project_root / item_obj.quarantine_path

        if not quar_path.exists():
            raise FileNotFoundError(f"Quarantined file not found at: {item_obj.quarantine_path}")

        # Ensure original directory exists
        orig_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file back
        shutil.move(str(quar_path), str(orig_path))

        # Update in database
        updated = await repo.restore_file(item_id)
        return updated
