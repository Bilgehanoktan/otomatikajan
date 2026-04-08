from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any

from apps.api.routers.auth.jwt_auth import get_current_user
from packages.skills.base import SkillRequest
from packages.skills.registry import skill_registry
from packages.skills.router import skill_router
from apps.api.services.skills_service import skills_service

router = APIRouter(prefix="/skills", tags=["Beceriler (Skills)"])


@router.get("", summary="Tüm becerileri listele")
async def list_skills(current_user=Depends(get_current_user)):
    return {
        "skills": skill_registry.ids(),
        "count": len(skill_registry.all())
    }


@router.get("/logs", summary="Becerilerin yürütme loglarını listele")
async def get_skill_logs(project_id: str | None = None, current_user=Depends(get_current_user)):
    return await skills_service.get_logs(project_id=project_id)


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
