"""
Sovereign AGI — Model Context Protocol (MCP) Server
Standardized Tool Interface for Agent Federation.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, select

from libs.db.models.core_models import Project, ProjectStatus
from libs.db.session import AsyncSessionLocal
from libs.mcp.tools import WorkflowDiagnosisInput, WorkflowReplayInput, replay_workflow as _replay_workflow, diagnose_failure as _diagnose_failure
from libs.mcp.registry import mcp_registry as MCPWorkflowRegistry

# Initialize FastMCP Server
mcp = FastMCP("SovereignAGI", instructions="Sovereign AGI MCP Server v13.0.4")

# Mock Security Config (In production, load from Vault/Secret Manager)
MCP_API_KEY = os.getenv("MCP_API_KEY", "agiv13_internal_key_default")

def validate_auth(key: str | None):
    if not key or key != MCP_API_KEY:
        raise ValueError("Unauthorized: Invalid or missing MCP_API_KEY")

@mcp.tool()
async def list_active_workflows() -> str:
    """List all workflows currently in RUNNING or PENDING state."""
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(Project).where(Project.status.in_([ProjectStatus.RUNNING, ProjectStatus.QUEUED]))
        )
        projects = res.scalars().all()

        if not projects:
            return "No active workflows found."

        lines = [f"- {p.title} ({p.id}) [Status: {p.status.value}]" for p in projects]
        return "Active Workflows:\n" + "\n".join(lines)

@mcp.tool()
async def trigger_workflow(title: str, api_key: str, template: str = "default", operator_id: str = "mcp_client") -> str:
    """Trigger a new Sovereign AGI workflow. Requires valid api_key."""
    try:
        validate_auth(api_key)
        from libs.db.repositories.repository import ProjectRepository
        from libs.workflow.persistence import WorkflowPersistence

        async with AsyncSessionLocal() as db:
            project = await ProjectRepository.create(
                db,
                title=title,
                description=f"MCP-triggered workflow: {title}",
                workflow_template=template,
                status=ProjectStatus.QUEUED
            )
            await db.commit()

            # Audit logging: MCP initiation event
            await WorkflowPersistence.save_event(
                project_id=str(project.id),
                event_type="mcp.workflow_initiated",
                payload={
                    "title": title,
                    "template": template,
                    "mcp_version": "13.0.4"
                },
                operator_id=operator_id
            )
            await db.commit()

            return f"Successfully queued workflow '{title}' with ID: {project.id}"
    except Exception as e:
        return f"Error triggering workflow: {str(e)}"

@mcp.tool()
async def get_system_health() -> dict[str, Any]:
    """Get high-level platform health metrics."""
    try:
        async with AsyncSessionLocal() as db:
            total = await db.execute(select(func.count(Project.id)))
            running = await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.RUNNING))
            errors = await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.ERROR))

            return {
                "platform": "Sovereign AGI",
                "version": "13.0.4",
                "status": "OPERATIONAL" if errors.scalar() == 0 else "DEGRADED",
                "metrics": {
                    "total_workflows": total.scalar(),
                    "active_nodes": running.scalar(),
                    "incident_count": errors.scalar()
                }
            }
    except Exception as e:
        return {"status": "UNAVAILABLE", "error": str(e)}

@mcp.tool()
async def replay_workflow(params: WorkflowReplayInput) -> str:
    """Securely replay a workflow from a specific step with optional overrides."""
    return await _replay_workflow(
        workflow_id=params.workflow_id,
        from_step_id=params.from_step_id,
        mode=params.mode,
        overrides=params.overrides,
        operator_id=params.operator_id,
        reason=params.reason
    )

@mcp.tool()
async def diagnose_workflow_failure(params: WorkflowDiagnosisInput) -> dict[str, Any]:
    """Perform metacognitive diagnosis on a failed workflow step via AI."""
    return await _diagnose_failure(
        workflow_id=params.workflow_id,
        step_id=params.step_id
    )

if __name__ == "__main__":
    # Start the server using stdio transport by default
    mcp.run()
