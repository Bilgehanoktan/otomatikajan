from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.routers.deps import get_skill_registry
from apps.bilgeapi.schemas.skills import SkillMetadataResponse

router = APIRouter(prefix="/v1")

@router.get("/catalog", tags=["Catalog"])
async def get_catalog(_identity: dict = Depends(require_permission("bilgeapi.incident.read"))):
    return {
        "diagnostics": [
            {
                "name": "mock_agent",
                "description": "Deterministic diagnostic simulator"
            }
        ],
        "repair_dispatchers": [
            {
                "name": "webhook",
                "description": "Secure payload dispatch webhook adapter"
            }
        ]
    }


@router.get("/catalog/skills", response_model=List[SkillMetadataResponse], tags=["Catalog"])
async def list_skills(
    _identity: dict = Depends(require_permission("bilgeapi.incident.read")),
    registry: Any = Depends(get_skill_registry)
):
    try:
        return registry.list_skills()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        ) from exc


@router.get("/catalog/skills/{skill_name}", response_model=SkillMetadataResponse, tags=["Catalog"])
async def get_skill(
    skill_name: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.read")),
    registry: Any = Depends(get_skill_registry)
):
    try:
        return registry.get_skill(skill_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        ) from exc


