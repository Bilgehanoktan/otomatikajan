import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIMaintenancePolicy
from .schemas import UIMaintenancePolicyCreate

class MaintenancePolicy:
    @staticmethod
    async def get_policy(db: AsyncSession, project_key: str) -> Optional[UIMaintenancePolicy]:
        result = await db.execute(select(UIMaintenancePolicy).filter(UIMaintenancePolicy.project_key == project_key))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_policy(db: AsyncSession, data: UIMaintenancePolicyCreate) -> UIMaintenancePolicy:
        policy = UIMaintenancePolicy(
            id=uuid.uuid4(),
            project_key=data.project_key,
            policy_name=data.policy_name,
            maintenance_window_json=data.maintenance_window,
            allowed_actions_json=data.allowed_actions,
            blocked_actions_json=data.blocked_actions,
            auto_repair_allowed=data.auto_repair_allowed,
            auto_apply_allowed=data.auto_apply_allowed,
            approval_required=data.approval_required,
            rollback_required=data.rollback_required
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def list_policies(db: AsyncSession) -> List[UIMaintenancePolicy]:
        result = await db.execute(select(UIMaintenancePolicy))
        return list(result.scalars().all())
