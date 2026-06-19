from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIRepairProjectProfile
from typing import Dict, Any, Optional

class ProjectPolicyRegistry:
    """Registry for project-specific safety and governance policies."""
    
    @staticmethod
    async def get_policy(db: AsyncSession, project_key: str) -> Dict[str, Any]:
        stmt = select(UIRepairProjectProfile).where(UIRepairProjectProfile.project_key == project_key)
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            return {}
        
        return {
            "safety": project.safety_policy_json or {},
            "governance": project.governance_policy_json or {},
            "auto_repair": project.auto_repair_enabled,
            "auto_apply": project.auto_apply_enabled,
            "approval_required": project.approval_required
        }

    @staticmethod
    async def update_policy(db: AsyncSession, project_key: str, safety: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None):
        stmt = select(UIRepairProjectProfile).where(UIRepairProjectProfile.project_key == project_key)
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()
        if project:
            if safety is not None:
                project.safety_policy_json = safety
            if governance is not None:
                project.governance_policy_json = governance
            await db.commit()
            return True
        return False
