import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIProjectOwnership
from .schemas import UIProjectOwnershipCreate

class OwnershipRegistry:
    @staticmethod
    async def get_project_ownership(db: AsyncSession, project_key: str) -> Optional[UIProjectOwnership]:
        result = await db.execute(select(UIProjectOwnership).filter(UIProjectOwnership.project_key == project_key))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_project_ownership(db: AsyncSession, data: UIProjectOwnershipCreate) -> UIProjectOwnership:
        ownership = UIProjectOwnership(
            id=uuid.uuid4(),
            project_key=data.project_key,
            owner_team_key=data.owner_team_key,
            technical_owner=data.technical_owner,
            business_owner=data.business_owner,
            escalation_level=data.escalation_level,
            backup_owner=data.backup_owner,
            approval_policy_json=data.approval_policy
        )
        db.add(ownership)
        await db.commit()
        await db.refresh(ownership)
        return ownership

    @staticmethod
    async def list_ownerships(db: AsyncSession) -> List[UIProjectOwnership]:
        result = await db.execute(select(UIProjectOwnership))
        return list(result.scalars().all())
