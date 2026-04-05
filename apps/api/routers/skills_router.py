from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any

from apps.api.routers.auth.jwt_auth import get_current_user
from skills.base import SkillRequest
from skills.registry import skill_registry
from skills.router import skill_router

router = APIRouter(prefix="/skills", tags=["Beceriler (Skills)"])


@router.get("", summary="Tüm becerileri listele")
async def list_skills(current_user=Depends(get_current_user)):
    return {
        "skills": skill_registry.ids(),
        "count": len(skill_registry.all())
    }


@router.get("/logs", summary="Becerilerin yürütme loglarını listele")
async def get_skill_logs(project_id: str | None = None, current_user=Depends(get_current_user)):
    from db.session import AsyncSessionLocal as get_db_session
    from db.models import SkillExecutionLog
    from sqlalchemy import select
    
    async with get_db_session() as db:
        stmt = select(SkillExecutionLog).order_by(SkillExecutionLog.created_at.desc()).limit(100)
        if project_id:
            stmt = stmt.filter(SkillExecutionLog.project_id == project_id)
            
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


@router.post("/suggest", summary="Görev için beceri öner")
async def suggest_skills(req: SkillRequest, current_user=Depends(get_current_user)):
    suggestions = skill_router.suggest(req)
    return {"suggestions": suggestions}


@router.post("/{skill_id}/run", summary="Belirli bir beceriyi manuel çalıştır")
async def run_skill(skill_id: str, req: SkillRequest, current_user=Depends(get_current_user)):
    skill = skill_registry.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill bulunamadı: {skill_id}")
    
    try:
        result = await skill.execute(req)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
