"""
Sovereign AGI — Model Context Protocol (MCP) Server
Standardized Tool Interface for Agent Federation.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select, func
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, ProjectStatus

# Initialize FastMCP Server
mcp = FastMCP("SovereignAGI", version="13.0.4")

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
async def trigger_workflow(title: str, template: str = "default") -> str:
    """Trigger a new Sovereign AGI workflow."""
    from libs.db.repositories.repository import ProjectRepository
    
    async with AsyncSessionLocal() as db:
        project = await ProjectRepository.create(
            db,
            title=title,
            workflow_template=template,
            status=ProjectStatus.QUEUED
        )
        await db.commit()
        
    # Enqueue task (Simulated for MCP tool - in real life this calls Celery)
    return f"Successfully queued workflow '{title}' with ID: {project.id}"

@mcp.tool()
async def get_system_health() -> Dict[str, Any]:
    """Get high-level platform health metrics."""
    async with AsyncSessionLocal() as db:
        total = await db.execute(select(func.count(Project.id)))
        running = await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.RUNNING))
        errors = await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.ERROR))
        
        return {
            "platform": "Sovereign AGI",
            "version": "13.0.4",
            "total_workflows": total.scalar(),
            "active_nodes": running.scalar(),
            "incident_count": errors.scalar(),
            "status": "OPERATIONAL" if errors.scalar() == 0 else "DEGRADED"
        }

if __name__ == "__main__":
    # Start the server using stdio transport by default
    mcp.run()
