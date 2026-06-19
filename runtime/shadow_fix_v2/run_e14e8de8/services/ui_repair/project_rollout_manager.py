import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIRepairProjectProfile
from .schemas import UIProjectProfileCreate

class ProjectRolloutManager:
    """Manages the creation and lifecycle of UI Repair Project Profiles."""
    
    @staticmethod
    async def create_project(db: AsyncSession, data: UIProjectProfileCreate):
        project = UIRepairProjectProfile(
            id=uuid.uuid4(),
            project_key=data.project_key,
            project_name=data.project_name,
            environment=data.environment,
            owner=data.owner,
            route_scope_json=data.route_scope,
            critical_routes_json=data.critical_routes,
            safety_policy_json=data.safety_policy,
            governance_policy_json=data.governance_policy,
            auto_repair_enabled=data.auto_repair_enabled,
            auto_apply_enabled=data.auto_apply_enabled,
            approval_required=data.approval_required,
            status="DRAFT",
            created_at=datetime.now(timezone.utc)
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def update_project_status(db: AsyncSession, project_key: str, status: str):
        stmt = select(UIRepairProjectProfile).where(UIRepairProjectProfile.project_key == project_key)
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()
        if project:
            project.status = status
            project.updated_at = datetime.now(timezone.utc)
            await db.commit()
        return project

    @staticmethod
    async def list_projects(db: AsyncSession):
        stmt = select(UIRepairProjectProfile).order_by(UIRepairProjectProfile.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_project(db: AsyncSession, project_key: str):
        stmt = select(UIRepairProjectProfile).where(UIRepairProjectProfile.project_key == project_key)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
