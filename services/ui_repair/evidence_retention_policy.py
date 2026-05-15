import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIEvidenceRetentionPolicy
from .schemas import UIEvidenceRetentionPolicyCreate

class EvidenceRetentionPolicy:
    @staticmethod
    async def list_policies(db: AsyncSession) -> List[UIEvidenceRetentionPolicy]:
        result = await db.execute(select(UIEvidenceRetentionPolicy))
        return list(result.scalars().all())

    @staticmethod
    async def create_policy(db: AsyncSession, data: UIEvidenceRetentionPolicyCreate) -> UIEvidenceRetentionPolicy:
        policy = UIEvidenceRetentionPolicy(
            id=uuid.uuid4(),
            policy_name=data.policy_name,
            retention_days=data.retention_days,
            evidence_type=data.evidence_type,
            archive_after_days=data.archive_after_days,
            delete_after_days=data.delete_after_days,
            legal_hold=data.legal_hold
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def get_policy_by_type(db: AsyncSession, evidence_type: str) -> Optional[UIEvidenceRetentionPolicy]:
        result = await db.execute(select(UIEvidenceRetentionPolicy).filter(UIEvidenceRetentionPolicy.evidence_type == evidence_type))
        return result.scalar_one_or_none()
        
    @staticmethod
    async def set_legal_hold(db: AsyncSession, policy_id: str, hold: bool) -> Optional[UIEvidenceRetentionPolicy]:
        result = await db.execute(select(UIEvidenceRetentionPolicy).filter(UIEvidenceRetentionPolicy.id == policy_id))
        policy = result.scalar_one_or_none()
        if policy:
            policy.legal_hold = hold
            await db.commit()
            await db.refresh(policy)
        return policy
