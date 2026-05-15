import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UICompatibilityCheck
from .schemas import UICompatibilityCheckCreate

class CompatibilityChecker:
    @staticmethod
    async def run_check(db: AsyncSession, project_key: str, version: str) -> UICompatibilityCheck:
        # Simulate compatibility logic
        # In a real scenario, this would check route registry, policy changes, etc.
        breaking_changes = []
        deprecated_features = []
        
        # Example check
        if project_key == "LEGACY_PROJECT":
            breaking_changes.append("Route registry format mismatch")
            deprecated_features.append("Markdown reports")
            
        status = "PASSED"
        if breaking_changes:
            status = "FAILED"
        elif deprecated_features:
            status = "WARNING"
            
        # Create evidence hash
        content_to_hash = {
            "project_key": project_key,
            "version": version,
            "breaking": breaking_changes,
            "deprecated": deprecated_features
        }
        evidence_hash = hashlib.sha256(json.dumps(content_to_hash, sort_keys=True).encode()).hexdigest()

        check = UICompatibilityCheck(
            id=uuid.uuid4(),
            project_key=project_key,
            version=version,
            status=status,
            breaking_changes_json=breaking_changes,
            deprecated_features_json=deprecated_features,
            migration_required=bool(breaking_changes),
            migration_notes="Upgrade to v2 schemas required" if breaking_changes else None,
            evidence_hash=evidence_hash
        )
        db.add(check)
        await db.commit()
        await db.refresh(check)
        return check

    @staticmethod
    async def get_latest_check(db: AsyncSession, project_key: str) -> Optional[UICompatibilityCheck]:
        result = await db.execute(select(UICompatibilityCheck).filter(UICompatibilityCheck.project_key == project_key).order_by(UICompatibilityCheck.checked_at.desc()))
        return result.scalar_one_or_none()
