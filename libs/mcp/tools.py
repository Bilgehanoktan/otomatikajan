"""
libs/mcp/tools.py — Phase 13.04.E
Standardized MCP Tool Registry for Sovereign AGI Federation.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from libs.workflow.engine import WorkflowEngine
from libs.db.session import AsyncSessionLocal
from libs.auth.rbac import is_authorized, Role

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

class MCPWorkflowRegistry:
    """Central registry for workflow-related MCP tools."""
    
    @staticmethod
    async def replay_workflow(params: WorkflowReplayInput) -> str:
        """Securely replay a workflow from a specific step with optional overrides."""
        # 1. RBAC Check (MCP Agents are 'OPERATORS' by default)
        if not is_authorized(Role.OPERATOR, "workflow:replay"):
             return "ERROR: MCP Agent (OPERATOR) unauthorized for deep replay. MANAGER role required."

        async with AsyncSessionLocal() as db:
            engine = WorkflowEngine(db)
            try:
                # Mode translation for engine
                mode_map = {
                    "same_input": "same_input",
                    "from_step": "from_step",
                    "with_override": "with_override"
                }
                
                await engine.replay(
                    workflow_id=params.workflow_id,
                    from_step_id=params.from_step_id,
                    mode=mode_map.get(params.mode, "same_input"),
                    overrides=params.overrides,
                    operator_id=params.operator_id,
                    reason=params.reason
                )
                return f"SUCCESS: Workflow {params.workflow_id} replayed from {params.from_step_id} in mode {params.mode}"
            except Exception as e:
                return f"FAILURE: Replay failed: {str(e)}"

    @staticmethod
    async def diagnose_failure(params: WorkflowDiagnosisInput) -> Dict[str, Any]:
        """Perform metacognitive diagnosis on a failed workflow step."""
        async with AsyncSessionLocal() as db:
            engine = WorkflowEngine(db)
            try:
                suggestion = await engine.suggest_fix(params.workflow_id, params.step_id)
                return {
                    "status": "COMPLETED",
                    "workflow_id": params.workflow_id,
                    "step_id": params.step_id,
                    "analysis": suggestion
                }
            except Exception as e:
                return {"status": "ERROR", "detail": str(e)}
