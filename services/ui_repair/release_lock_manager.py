import logging
import uuid
import hashlib
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIReleaseLock, UIFinalAuditPack, ReleaseStatus

logger = logging.getLogger(__name__)

class ReleaseLockManager:
    """Phase 30: Manages the final release locking mechanism."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _resolve_commit_sha() -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode == 0:
                value = result.stdout.strip()
                return value or None
        except Exception:
            logger.exception("Failed to resolve current git SHA for release lock.")
        return None

    async def create_release_lock(self, version: str, locked_by: str, audit_pack_id: uuid.UUID) -> UIReleaseLock:
        """Creates an immutable release lock for a verified version."""
        release_key = f"RELEASE-{version.replace('.', '-')}-{uuid.uuid4().hex[:4].upper()}"
        logger.info(f"Creating Release Lock: {release_key} (v{version})")
        
        # Verify audit pack exists and passed
        stmt = select(UIFinalAuditPack).where(UIFinalAuditPack.id == audit_pack_id)
        result = await self.db.execute(stmt)
        pack = result.scalar_one_or_none()
        
        if not pack or pack.status != ReleaseStatus.PASSED:
            logger.error(f"Cannot lock release: Audit pack {audit_pack_id} not found or not passed.")
            raise ValueError(f"Audit pack {audit_pack_id} is missing or not in PASSED state.")

        summary_json = dict(pack.summary_json or {})
        summary_payload = {
            "audit_pack_id": str(pack.id),
            "audit_pack_key": pack.pack_key,
            "audit_pack_status": pack.status.value if hasattr(pack.status, "value") else str(pack.status),
            "audit_pack_evidence_hash": pack.evidence_hash,
            "audit_pack_generated_at": pack.generated_at.isoformat() if pack.generated_at else None,
            "summary": summary_json,
        }
        evidence_hash = hashlib.sha256(
            str(summary_payload).encode("utf-8", errors="replace")
        ).hexdigest()
        
        lock = UIReleaseLock(
            release_key=release_key,
            version=version,
            status=ReleaseStatus.SEALED,
            locked_by=locked_by,
            locked_at=datetime.now(timezone.utc),
            commit_sha=self._resolve_commit_sha(),
            test_summary_json=summary_payload,
            audit_pack_id=audit_pack_id,
            release_notes=f"Official Release Candidate for Sovereign AGI Control Plane v{version}.",
            evidence_hash=f"SHA256:{evidence_hash}"
        )
        
        self.db.add(lock)
        await self.db.commit()
        await self.db.refresh(lock)
        
        logger.info(f"Release Lock created: {release_key}")
        return lock

    async def get_latest_lock(self) -> Optional[UIReleaseLock]:
        stmt = select(UIReleaseLock).order_by(UIReleaseLock.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
