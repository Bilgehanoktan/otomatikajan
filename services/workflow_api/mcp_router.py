"""
services/workflow_api/mcp_router.py — Phase 13.05
Standardized MCP Configuration and Discovery API.
"""
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from libs.config import MCP_SERVERS
from services.auth.jwt_auth import require_permission

router = APIRouter(tags=["MCP Hub"])

class McpServerConfig(BaseModel):
    command: str
    args: list[str]
    env: dict[str, str] = {}
    enabled: bool = True
    type: str = "stdio"
    description: str = "Automated MCP Server"

class McpConfigResponse(BaseModel):
    status: str = "success"
    data: dict[str, Any]

@router.get("/config", response_model=McpConfigResponse)
@router.get("/config/", response_model=McpConfigResponse)
async def get_mcp_config(
    identity: dict[str, Any] = Depends(require_permission("mcp.view"))
):
    """
    Returns the list of configured MCP servers for this node.
    Used by the MCP Hub dashboard for visualization and status monitoring.
    """
    return {
        "status": "success",
        "data": {
            "mcp_servers": MCP_SERVERS,
            "version": "13.0.5",
            "active_node": "sovereign-core-01"
        }
    }
