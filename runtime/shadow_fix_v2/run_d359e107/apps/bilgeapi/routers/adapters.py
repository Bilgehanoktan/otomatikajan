from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.adapters.registry import adapter_registry

router = APIRouter(prefix="/v1")

class AdapterListItem(BaseModel):
    name: str = Field(..., description="Unique name of the adapter")
    enabled: bool = Field(..., description="Whether the adapter is enabled in configuration")
    configured: bool = Field(..., description="Whether all required settings are configured")
    health: str = Field(..., description="Current health status (healthy, unhealthy, disabled, not_configured)")

class AdapterHealthResponse(BaseModel):
    name: str = Field(..., description="Adapter name")
    enabled: bool = Field(..., description="Whether the adapter is enabled")
    configured: bool = Field(..., description="Whether required settings are configured")
    health: str = Field(..., description="Current health status")
    last_checked_at: str = Field(..., description="ISO 8601 timestamp of health check")

@router.get("/adapters", response_model=List[AdapterListItem], tags=["Adapters"])
async def list_adapters(
    _identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Lists all external dispatch adapters and their general status.
    """
    adapters = adapter_registry.list_adapters()
    res = []
    for adapter in adapters:
        health_status = await adapter.health_check()
        res.append(
            AdapterListItem(
                name=adapter.name,
                enabled=adapter.enabled,
                configured=adapter.configured,
                health=health_status
            )
        )
    return res

@router.get("/adapters/{name}/health", response_model=AdapterHealthResponse, tags=["Adapters"])
async def get_adapter_health(
    name: str,
    _identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Gets the detailed health status of a specific adapter.
    """
    adapter = adapter_registry.get_adapter(name)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Adapter '{name}' not found.")

    health_status = await adapter.health_check()
    return AdapterHealthResponse(
        name=adapter.name,
        enabled=adapter.enabled,
        configured=adapter.configured,
        health=health_status,
        last_checked_at=datetime.now(timezone.utc).isoformat()
    )
