"""
libs/mcp/tools.py — Phase 15.01
Standardized MCP Tool Registry for Sovereign AGI Federation.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from libs.workflow.engine import WorkflowEngine
from libs.db.session import AsyncSessionLocal
from libs.auth.rbac import is_authorized, Role
from libs.mcp.registry import mcp_registry

class WorkflowReplayInput(BaseModel):
    workflow_id: str = Field(..., description="UUID of the workflow to replay")
    from_step_id: str = Field(..., description="Step ID to start replay from")
    mode: str = Field("same_input", description="Replay mode: same_input, from_step, with_override")
    overrides: Optional[Dict[str, Any]] = Field(None, description="Input overrides if mode is with_override")
    operator_id: str = Field("mcp_agent", description="The ID of the autonomous agent initiating the replay")
    reason: str = Field("Autonomous recovery initiated via MCP", description="Audit reason")

class WorkflowDiagnosisInput(BaseModel):
    workflow_id: str = Field(..., description="UUID of the workflow")
    step_id: str = Field(..., description="Step ID to diagnose")

@mcp_registry.register(name="replay_workflow", requires_approval=True)
async def replay_workflow(workflow_id: str, from_step_id: str, mode: str = "same_input", overrides: Optional[Dict[str, Any]] = None, operator_id: str = "mcp_agent", reason: str = "Autonomous recovery"):
    """Securely replay a workflow from a specific step with optional overrides."""
    # 1. RBAC Check
    if not is_authorized(Role.OPERATOR, "workflow:replay"):
         return "ERROR: MCP Agent (OPERATOR) unauthorized for deep replay. MANAGER role required."

    async with AsyncSessionLocal() as db:
        engine = WorkflowEngine(db)
        try:
            await engine.replay(
                workflow_id=workflow_id,
                from_step_id=from_step_id,
                mode=mode,
                overrides=overrides,
                operator_id=operator_id,
                reason=reason
            )
            return f"SUCCESS: Workflow {workflow_id} replayed from {from_step_id}"
        except Exception as e:
            return f"FAILURE: Replay failed: {str(e)}"

@mcp_registry.register(name="diagnose_failure")
async def diagnose_failure(workflow_id: str, step_id: str):
    """Perform metacognitive diagnosis on a failed workflow step."""
    async with AsyncSessionLocal() as db:
        engine = WorkflowEngine(db)
        try:
            suggestion = await engine.suggest_fix(workflow_id, step_id)
            return {
                "status": "COMPLETED",
                "workflow_id": workflow_id,
                "step_id": step_id,
                "analysis": suggestion
            }
        except Exception as e:
            return {"status": "ERROR", "detail": str(e)}
