import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIOperationsTeam
from .schemas import UIOperationsTeamCreate

class OperationsModel:
    @staticmethod
    async def list_teams(db: AsyncSession) -> List[UIOperationsTeam]:
        result = await db.execute(select(UIOperationsTeam))
        return list(result.scalars().all())

    @staticmethod
    async def create_team(db: AsyncSession, data: UIOperationsTeamCreate) -> UIOperationsTeam:
        team = UIOperationsTeam(
            id=uuid.uuid4(),
            team_key=data.team_key,
            team_name=data.team_name,
            responsibilities_json=data.responsibilities,
            owned_project_keys_json=data.owned_project_keys,
            escalation_channels_json=data.escalation_channels,
            oncall_policy_json=data.oncall_policy,
            status=data.status
        )
        db.add(team)
        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def get_team(db: AsyncSession, team_key: str) -> Optional[UIOperationsTeam]:
        result = await db.execute(select(UIOperationsTeam).filter(UIOperationsTeam.team_key == team_key))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_team_status(db: AsyncSession, team_key: str, status: str) -> Optional[UIOperationsTeam]:
        result = await db.execute(select(UIOperationsTeam).filter(UIOperationsTeam.team_key == team_key))
        team = result.scalar_one_or_none()
        if team:
            team.status = status
            await db.commit()
            await db.refresh(team)
        return team
