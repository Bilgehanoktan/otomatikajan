import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIReleaseRecord
from .schemas import UIReleaseRecordCreate

class ReleaseNotesGenerator:
    @staticmethod
    async def generate_release_record(db: AsyncSession, data: UIReleaseRecordCreate) -> UIReleaseRecord:
        # Create evidence hash
        content_to_hash = {
            "version": data.version,
            "changes": data.changes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        evidence_hash = hashlib.sha256(json.dumps(content_to_hash, sort_keys=True).encode()).hexdigest()
        
        record = UIReleaseRecord(
            id=uuid.uuid4(),
            version=data.version,
            release_type=data.release_type,
            project_keys_json=data.project_keys,
            summary=data.summary,
            changes_json=data.changes,
            risk_summary_json=data.risk_summary,
            compatibility_notes=data.compatibility_notes,
            rollback_notes=data.rollback_notes,
            evidence_hash=evidence_hash
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def list_releases(db: AsyncSession) -> List[UIReleaseRecord]:
        result = await db.execute(select(UIReleaseRecord).order_by(UIReleaseRecord.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_release(db: AsyncSession, release_id: str) -> Optional[UIReleaseRecord]:
        result = await db.execute(select(UIReleaseRecord).filter(UIReleaseRecord.id == release_id))
        return result.scalar_one_or_none()
