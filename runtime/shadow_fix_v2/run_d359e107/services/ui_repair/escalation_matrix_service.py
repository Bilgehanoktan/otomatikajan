from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .ownership_registry import OwnershipRegistry
from .operations_model import OperationsModel

class EscalationMatrixService:
    @staticmethod
    async def get_escalation_path(db: AsyncSession, project_key: str, severity: str) -> Dict[str, Any]:
        ownership = await OwnershipRegistry.get_project_ownership(db, project_key)
        if not ownership:
            return {"status": "NO_OWNER_DEFINED", "fallback": "CENTRAL_OPS"}
            
        team = await OperationsModel.get_team(db, ownership.owner_team_key)
        if not team:
            return {"status": "TEAM_NOT_FOUND", "fallback": "CENTRAL_OPS"}
            
        escalation_channels = team.escalation_channels_json
        
        # Simple routing logic
        channel = escalation_channels.get(severity, escalation_channels.get("DEFAULT", "DASHBOARD"))
        
        return {
            "project": project_key,
            "owner_team": team.team_name,
            "technical_owner": ownership.technical_owner,
            "business_owner": ownership.business_owner,
            "escalation_level": ownership.escalation_level,
            "channel": channel,
            "status": "ROUTED"
        }
