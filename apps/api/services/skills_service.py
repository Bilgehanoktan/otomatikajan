from uuid import UUID
from sqlalchemy import select
from packages.persistence.session import AsyncSessionLocal as get_db_session
from packages.persistence.models import SkillExecutionLog

class SkillsService:
    @staticmethod
    async def get_logs(project_id: str | None = None, limit: int = 100):
        async with get_db_session() as db:
            stmt = select(SkillExecutionLog).order_by(SkillExecutionLog.created_at.desc()).limit(limit)
            if project_id:
                try:
                    valid_id = UUID(project_id)
                    stmt = stmt.filter(SkillExecutionLog.project_id == valid_id)
                except (ValueError, TypeError):
                    pass
                
            result = await db.execute(stmt)
            logs = result.scalars().all()
            
            return [
                {
                    "id": str(log.id),
                    "project_id": str(log.project_id) if log.project_id else None,
                    "agent_id": log.agent_id,
                    "skill_id": log.skill_id,
                    "success": log.success,
                    "summary": log.summary,
                    "data": log.data,
                    "errors": log.errors,
                    "duration_s": log.duration_s,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                } for log in logs
            ]

skills_service = SkillsService()
