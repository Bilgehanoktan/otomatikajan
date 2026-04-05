"""
Specialists Router — Faz 8 Infra
Exposes loaded agency specialists to the UI.
"""
from fastapi import APIRouter, Depends
from auth.jwt_auth import get_current_user
from core.agency.loader import get_agency_loader

router = APIRouter(prefix="/specialists", tags=["Agency"])

@router.get("")
async def list_specialists(current_user=Depends(get_current_user)):
    """
    Yüklü uzmanları listele.
    """
    loader = get_agency_loader()
    specialists = []
    # personas contains loaded agents
    for agent_id, p in loader.personas.items():
        specialists.append({
            "id": agent_id,
            "name": p.get("name", agent_id.replace("-", " ").title()),
            "role": p.get("role", p.get("category", "Specialist")),
            "description": p.get("description", ""),
            "skills": p.get("tools", []),
            "color": p.get("color", "blue"),
            "emoji": p.get("emoji", "🤖"),
            "prompt": p.get("system_prompt", "")
        })
    return {"specialists": specialists}
