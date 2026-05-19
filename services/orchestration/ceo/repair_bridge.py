from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# ── Response & Request Schemas ──────────────────────────────────────────

class CEOFindingPayload(BaseModel):
    finding_id: str
    title: str
    description: str
    category: str
    priority_score: float = 0.0
    source_signal: str = "CEO_ENGINE"
    affected_route: str | None = None
    affected_endpoint: str | None = None
    affected_files: list[str] = []
    recommended_action: str | None = None
    recommended_agent: str | None = None
    requested_mode: str | None = None
    can_trigger_repair: bool = True
    status: str = "open"
    repair_case_id: str | None = None


class RepairCaseInput(BaseModel):
    incident_id: str
    finding_id: str
    failing_test: str = ""
    stack_trace: str = ""
    affected_files: list[str] = []
    affected_route: str | None = None
    affected_endpoint: str | None = None
    reproduction_command: str | None = None
    expected_behavior: str = ""
    actual_behavior: str = ""
    constraints: list[str] = []
    risk_limit: str = "conservative"
    recommended_agent: str = "swe_agent"
    requested_mode: str = "local_adapter"


class ExternalRepairRequest(BaseModel):
    finding: CEOFindingPayload
    auto_start: bool = Field(default=False)


class RepairCaseBuildResult(BaseModel):
    status: str = "created"
    finding_id: str
    repair_case_id: str
    incident_id: str
    artifact_ref: str
    recommended_agent: str
    requested_mode: str
    next_step: str = "start_self_repair_taskflow"
    case_input: RepairCaseInput


# ── Bridge Implementation ─────────────────────────────────────────────

def build_repair_case_from_finding(finding: CEOFindingPayload | dict[str, Any]) -> RepairCaseBuildResult:
    """
    Converts a CEO finding or raw payload into a validated RepairCaseInput and writes a repair_case.json artifact.
    """
    # 1. Extract finding_id
    if isinstance(finding, dict):
        finding_id = finding.get("finding_id")
    else:
        finding_id = finding.finding_id

    if not finding_id:
        raise ValueError("finding_id is required to bridge CEO finding to repair case")

    # Coerce dict to CEOFindingPayload
    if isinstance(finding, dict):
        payload = CEOFindingPayload(**finding)
    else:
        payload = finding

    # 2. Stable unique incident_id generation
    # Build a stable seed based on finding_id
    seed_hash = hashlib.sha256(payload.finding_id.encode("utf-8")).hexdigest()[:12].upper()
    incident_id = f"INC-CEO-{seed_hash}"

    # 3. Generate reproduction command
    reproduction_cmd = None
    if payload.affected_endpoint or payload.affected_route:
        route = payload.affected_endpoint or payload.affected_route
        reproduction_cmd = f"curl -X POST http://localhost:8000{route}"

    # 4. Set defaults
    agent = payload.recommended_agent or "swe_agent"
    mode = payload.requested_mode or "local_adapter"

    # Validate catalog compatibility for safety
    allowed_agents = {"swe_agent", "swe_rex", "pr_agent", "stagehand", "openhands", "github_copilot"}
    if agent not in allowed_agents:
        agent = "swe_agent"

    allowed_modes = {"local_adapter", "sandbox_runner", "review_gate", "experimental"}
    if mode not in allowed_modes:
        mode = "local_adapter"

    case_input = RepairCaseInput(
        incident_id=incident_id,
        finding_id=payload.finding_id,
        affected_files=payload.affected_files,
        affected_route=payload.affected_route,
        affected_endpoint=payload.affected_endpoint,
        reproduction_command=reproduction_cmd,
        recommended_agent=agent,
        requested_mode=mode,
        risk_limit="conservative",
    )

    # 5. Safe Artifact Path Writing (strictly under repair_outputs/{incident_id}/)
    workspace_root = Path("e:/ai_company_faz12.1").resolve()
    outputs_base = (workspace_root / "repair_outputs").resolve()
    
    # Path traversal protection
    incident_dir = (outputs_base / incident_id).resolve()
    artifact_path = (incident_dir / "repair_case.json").resolve()
    
    if not str(incident_dir).startswith(str(outputs_base)):
        raise ValueError("Path traversal violation detected: attempted write outside repair_outputs/")

    # Ensure output folder exists safely
    incident_dir.mkdir(parents=True, exist_ok=True)

    # Write serialized stable JSON without secret dumps
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(case_input.model_dump(), f, indent=2, sort_keys=True)

    # Return structured result
    relative_ref = f"repair_outputs/{incident_id}/repair_case.json"
    
    return RepairCaseBuildResult(
        status="created",
        finding_id=payload.finding_id,
        repair_case_id=payload.finding_id,  # Map finding_id directly to repair_case_id
        incident_id=incident_id,
        artifact_ref=relative_ref,
        recommended_agent=agent,
        requested_mode=mode,
        case_input=case_input,
    )


async def start_self_repair_from_repair_case(
    case_input: RepairCaseInput,
    auto_start: bool = False,
    db: AsyncSession | None = None
) -> dict[str, Any]:
    """
    Bridges RepairCaseInput to a real self_repair TaskFlow run in Phase 3.
    """
    if not auto_start:
        return {
            "status": "not_started",
            "incident_id": case_input.incident_id,
            "message": "Repair case prepared. Awaiting human-in-the-loop manual approval to trigger."
        }

    if db is None:
        raise ValueError("Database session (db) is required when auto_start is True")

    # 1. Programmatically create a Project using ProjectRepository.create
    from libs.db.repositories.repository import ProjectRepository
    from libs.db.models import ProjectStatus

    title = f"Self Repair Case: {case_input.incident_id}"
    description = f"Auto-generated repair for finding {case_input.finding_id}"

    # Task execution context mapping for self_repair template step 1
    exec_context = {
        "incident_id": case_input.incident_id,
        "source": "ceo_finding",
        "finding_id": case_input.finding_id,
        "failing_test": case_input.failing_test or None,
        "stack_trace": case_input.stack_trace or None,
        "affected_files": case_input.affected_files or [],
        "reproduction_command": case_input.reproduction_command,
        "expected_behavior": case_input.expected_behavior or "",
        "actual_behavior": case_input.actual_behavior or "",
        "constraints": case_input.constraints or [],
        "recommended_agent": case_input.recommended_agent,
        "requested_mode": case_input.requested_mode,
        "risk_limit": case_input.risk_limit,
    }

    project = await ProjectRepository.create(
        db=db,
        title=title,
        description=description,
        source="CONTROL_PLANE",
        priority="HIGH",
        workflow_template="self_repair",
        quality_profile="standard",
        execution_context=exec_context,
        status=ProjectStatus.QUEUED.value
    )
    await db.commit()

    # 2. Enqueue the project run via job_queue.enqueue
    from services.orchestration.application.job_queue import job_queue
    job = await job_queue.enqueue(
        "run_project",
        project_id=str(project.id),
        title=project.title,
        description=project.description or "",
        workflow_template=project.workflow_template or "self_repair",
        quality_profile=project.quality_profile or "standard",
    )

    # Update job_id in Project
    project.job_id = job.id
    await db.commit()

    # 3. Write taskflow_run.json under repair_outputs/{incident_id}/taskflow_run.json
    workspace_root = Path("e:/ai_company_faz12.1").resolve()
    outputs_base = (workspace_root / "repair_outputs").resolve()
    incident_dir = (outputs_base / case_input.incident_id).resolve()
    
    # Path traversal protection
    if not str(incident_dir).startswith(str(outputs_base)):
        raise ValueError("Path traversal violation detected: attempted write outside repair_outputs/")
        
    incident_dir.mkdir(parents=True, exist_ok=True)
    run_path = incident_dir / "taskflow_run.json"
    
    with open(run_path, "w", encoding="utf-8") as f:
        json.dump({
            "project_id": str(project.id),
            "job_id": job.id,
            "status": "queued",
            "workflow_template": "self_repair"
        }, f, indent=2, sort_keys=True)

    return {
        "status": "initiated",
        "taskflow_id": str(project.id),
        "incident_id": case_input.incident_id,
        "message": "Self repair TaskFlow run started successfully.",
        "job_id": job.id
    }
