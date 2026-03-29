# filepath: api/mcp_router.py
"""
Model Context Protocol (MCP) Router — Lightweight metadata endpoint.

Exposes project structure, DB schema, and OpenAPI spec as MCP resources.
Tool endpoints are auth-guarded to prevent unauthorized use.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from pathlib import Path

from auth.jwt_auth import optional_admin
from observability.logging import get_logger

logger = get_logger("api.mcp")

router = APIRouter(prefix="/mcp", tags=["MCP"])


class MCPResource(BaseModel):
    uri: str
    name: str
    description: str
    mimeType: str = "text/plain"


class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]


# ── Resources ──────────────────────────────────────────────
@router.get("/resources", summary="List MCP Resources")
async def list_resources() -> List[MCPResource]:
    """Exposes project metadata and code as MCP resources."""
    return [
        MCPResource(
            uri="mcp://project/db-schema",
            name="Database Schema",
            description="SQLAlchemy models defining the system database structure.",
            mimeType="text/x-python",
        ),
        MCPResource(
            uri="mcp://project/api-spec",
            name="API Documentation",
            description="OpenAPI specification for the AI Company services.",
            mimeType="application/json",
        ),
        MCPResource(
            uri="mcp://project/folder-structure",
            name="Project Structure",
            description="Recursive list of all project directories and files.",
            mimeType="text/plain",
        ),
    ]


@router.get("/resources/read", summary="Read MCP Resource")
async def read_resource(uri: str, request: Request):
    """Reads the content of a specific MCP resource."""
    root = Path(os.getcwd())

    if uri == "mcp://project/db-schema":
        model_path = root / "db" / "models.py"
        if model_path.exists():
            return {"uri": uri, "content": model_path.read_text(encoding="utf-8")}
        raise HTTPException(status_code=404, detail="db/models.py not found")

    if uri == "mcp://project/api-spec":
        # Serve the live OpenAPI spec from the running FastAPI app
        app = request.app
        openapi_schema = app.openapi()
        return {"uri": uri, "content": openapi_schema}

    if uri == "mcp://project/folder-structure":
        tree = _build_project_tree(root, max_depth=3)
        return {"uri": uri, "content": tree}

    raise HTTPException(status_code=404, detail="Resource not found")


# ── Tools ──────────────────────────────────────────────────
@router.get("/tools", summary="List MCP Tools")
async def list_tools() -> List[MCPTool]:
    """Exposes internal system tools to external AI agents."""
    return [
        MCPTool(
            name="visual_sentinel_check",
            description="Trigger a UI regression check for a specific component.",
            inputSchema={
                "type": "object",
                "properties": {
                    "component": {"type": "string", "description": "e.g. dashboard_main"}
                },
                "required": ["component"],
            },
        ),
        MCPTool(
            name="autonomous_patch",
            description="Search and fix unawaited coroutines in a file.",
            inputSchema={
                "type": "object",
                "properties": {"file_path": {"type": "string"}},
                "required": ["file_path"],
            },
        ),
    ]


@router.post(
    "/tools/execute",
    summary="Execute an MCP Tool (admin only)",
    dependencies=[Depends(optional_admin)],
)
async def execute_tool(body: dict):
    """Execute a named MCP tool. Requires admin authentication."""
    tool_name = body.get("name", "")
    if not tool_name:
        raise HTTPException(status_code=422, detail="Tool name required")

    logger.info(f"MCP tool execution requested: {tool_name}")

    # Placeholder — tool execution routing would go here
    raise HTTPException(
        status_code=501,
        detail=f"Tool '{tool_name}' execution not yet implemented",
    )


# ── Helpers ────────────────────────────────────────────────
SKIP_DIRS = {
    "__pycache__", ".git", ".pytest_cache", "node_modules",
    ".vscode", ".idea", "uploads", "workspace", "tmp",
    ".deer-flow", "vendor", "temiz_proje.zip",
}


def _build_project_tree(root: Path, max_depth: int = 3) -> str:
    """Walk the project directory tree and return a formatted string."""
    lines: list[str] = []

    def _walk(path: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        dirs = [e for e in entries if e.is_dir() and e.name not in SKIP_DIRS]
        files = [e for e in entries if e.is_file()]

        for d in dirs:
            lines.append(f"{prefix}{d.name}/")
            _walk(d, prefix + "  ", depth + 1)

        for f in files[:20]:  # Cap files per dir to keep output manageable
            lines.append(f"{prefix}{f.name}")
        if len(files) > 20:
            lines.append(f"{prefix}... and {len(files) - 20} more files")

    lines.append(f"{root.name}/")
    _walk(root, "  ", 1)
    return "\n".join(lines)
