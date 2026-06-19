"""
Workflow Control Plane API — Phase 13.04
Exposes workflow runs, step details, retry/replay, and approval controls.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from libs.db.session import AsyncSessionLocal, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth.jwt_auth import require_method_permission, require_permission

router = APIRouter(
    prefix="/workflows",
    tags=["Workflow Control Plane"],
    dependencies=[Depends(require_method_permission("workflow.view", "workflow.approve"))],
)
logger = logging.getLogger("services.workflow_api.router")
_EPHEMERAL_WORKFLOWS: dict[str, dict[str, Any]] = {}


def _workflow_template_step_count(workflow_template: str | None) -> int:
    from libs.workflow.registry import WorkflowRegistry

    definition = WorkflowRegistry.get_definition(workflow_template or "default")
    return len(definition.steps)


def _planned_steps_for_template(workflow_template: str | None) -> list[StepOut]:
    from libs.workflow.registry import WorkflowRegistry

    definition = WorkflowRegistry.get_definition(workflow_template or "default")
    return [
        StepOut(
            id=template.id,
            name=template.id,
            action=template.action,
            status="pending",
            retries=0,
            max_retries=3,
            dependencies=template.depends_on,
            output_summary=template.description,
        )
        for template in definition.steps
    ]


def _is_active_workflow_status(status_value: str | None) -> bool:
    return str(status_value or "").lower() in {
        "queued",
        "pending",
        "running",
        "resuming",
        "replaying",
        "waiting_approval",
        "pending_approval",
    }


def _is_reassignable_workflow_status(status_value: str | None) -> bool:
    return str(status_value or "").lower() in {
        "cancelled",
        "canceled",
        "failed",
        "error",
        "interrupted",
        "paused",
    }


# ── Response Schemas ──────────────────────────────────────────────────────────

class StepOut(BaseModel):
    id: str
    name: str
    action: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retries: int = 0
    max_retries: int = 3
    error: str | None = None
    dependencies: list[str] = []
    output_summary: str | None = None


class WorkflowOut(BaseModel):
    id: str
    name: str
    workflow_type: str
    status: str
    source: str
    steps: list[StepOut]
    context_keys: list[str]
    payload: dict[str, Any] = {}
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    final_report: str | None = None
    history: list[dict[str, Any]] = []
    related_approvals: list[dict[str, Any]] = []
    related_incidents: list[dict[str, Any]] = []


class ProjectListItem(BaseModel):
    id: str
    title: str
    status: str
    workflow_type: str
    progress_pct: int
    created_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    total_steps: int
    completed_steps: int
    failed_steps: int
    has_active_workflow: bool


class RetryResponse(BaseModel):
    message: str
    task_id: str


class ReplayRequest(BaseModel):
    from_step: str
    mode: str = "same_input"  # same_input, from_step, with_override
    overrides: dict[str, Any] | None = None
    reason: str               # Audit requirement: why is this being replayed?
    operator_id: str          # Audit requirement: who is replaying?

class ApprovalRequest(BaseModel):
    operator_id: str
    notes: str = ""


class ReassignRequest(BaseModel):
    operator_id: str = "admin_human"
    reason: str = "Operator requested reassign after terminal workflow state."
    reset_steps: bool = True
    preserve_completed_steps: bool = True
    assigned_agent: str | None = None


class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    workflow_template: str = "default"
    quality_profile: str = "standard"
    priority: str = "medium"


class ImprovementOut(BaseModel):
    id: str
    opportunity_id: str
    target_file: str
    instruction: str
    proposed_patch: str
    status: str
    created_at: datetime
    test_results: dict[str, Any] | None = None





# ── Helpers ───────────────────────────────────────────────────────────────────

# ── Helpers ───────────────────────────────────────────────────────────────────
async def _resolve_project_id(db, project_id: str):
    """
    Resolves a full UUID or short-ID prefix to a validated Project.id (uuid.UUID).
    """
    from sqlalchemy import String, cast, func, select

    from libs.db.models.core_models import Project

    uid = None
    try:
        uid = uuid.UUID(project_id)
    except ValueError:
        pass

    if uid:
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project.id
    else:
        clean_id = project_id.replace("-", "").lower()
        if len(clean_id) < 8:
            raise HTTPException(status_code=400, detail="ID prefix too short. Min 8 hex chars required.")

        res = await db.execute(
            select(Project).where(
                func.lower(func.replace(cast(Project.id, String), "-", "")).like(f"{clean_id}%")
            )
        )
        matches = res.scalars().all()
        if not matches:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        if len(matches) > 1:
            raise HTTPException(status_code=300, detail=f"Ambiguous ID '{project_id}'. {len(matches)} matches.")
        return matches[0].id

async def _get_project_with_subtasks(project_id: str):
    """Load project + subtasks from DB with Flexible ID Resolution."""
    from sqlalchemy import select

    from libs.db.models.core_models import Project, SubTask
    from libs.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        resolved_uid = await _resolve_project_id(db, project_id)

        res = await db.execute(select(Project).where(Project.id == resolved_uid))
        project = res.scalar_one_or_none()

        res_st = await db.execute(
            select(SubTask).where(SubTask.project_id == resolved_uid).order_by(SubTask.created_at)
        )
        subtasks = res_st.scalars().all()
        return project, subtasks


async def _dispatch_project_job(payload: dict[str, Any]) -> None:
    """Dispatch queue work outside the request/response critical path."""
    from services.orchestration.application.job_queue import job_queue

    try:
        await job_queue.enqueue("run_project", **payload)
    except Exception:
        logger.exception("Workflow queue dispatch failed for project %s", payload.get("project_id"))


def _build_ephemeral_workflow(
    workflow_id: str,
    req: ProjectCreate,
    *,
    status: str = "queued",
) -> dict[str, Any]:
    now = datetime.now(UTC)
    planned_steps = _planned_steps_for_template(req.workflow_template or "default")
    return {
        "id": workflow_id,
        "title": req.title,
        "name": req.title,
        "description": req.description,
        "status": status,
        "workflow_type": req.workflow_template or "default",
        "quality_profile": req.quality_profile or "standard",
        "source": "control_plane",
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "progress_pct": 0,
        "total_steps": len(planned_steps),
        "completed_steps": 0,
        "failed_steps": 0,
        "has_active_workflow": True,
        "steps": planned_steps,
        "history": [],
        "payload": {
            "description": req.description,
            "quality_profile": req.quality_profile or "standard",
        },
        "context_keys": [],
        "related_approvals": [],
        "related_incidents": [],
        "final_report": None,
    }


def _prefer_ephemeral_workflows() -> bool:
    # Ephemeral workflows are intentionally opt-in. The default API contract must
    # persist created workflows so list/detail/approve/cancel operate on one store.
    return os.getenv("EPHEMERAL_WORKFLOWS_ENABLED", "false").lower() == "true"


def _map_workflow(project, subtasks) -> WorkflowOut:
    steps = []
    for st in subtasks:
        status_val = st.status.value if hasattr(st.status, "value") else str(st.status)
        output_summary = None
        if st.result:
            output_summary = st.result[:200] + ("..." if len(st.result) > 200 else "")
        steps.append(StepOut(
            id=str(st.id),
            name=st.agent_id,
            action=st.agent_id,
            status=status_val.lower(),
            started_at=None,
            completed_at=st.completed_at,
            retries=st.attempts or 0,
            max_retries=3,
            error=getattr(st, "causal_anchor", None) if status_val.lower() in ("error", "failed") else None,
            dependencies=st.dependencies if isinstance(st.dependencies, list) else [],
            output_summary=output_summary,
        ))

    if not steps:
        steps = _planned_steps_for_template(project.workflow_template or "default")

    p_status = project.status.value if hasattr(project.status, "value") else str(project.status)
    ctx_keys = list((project.execution_context or {}).keys())
    report = (project.execution_context or {}).get("final_report") or project.report or None

    return WorkflowOut(
        id=str(project.id),
        name=project.title,
        workflow_type=project.workflow_template or "default",
        status=p_status.lower(),
        source=project.source.value if hasattr(project.source, "value") else str(project.source),
        steps=steps,
        context_keys=ctx_keys,
        payload=project.execution_context or {},
        created_at=project.created_at,
        started_at=project.started_at,
        completed_at=project.completed_at,
        final_report=report,
        history=[],  # Will be populated by the caller if needed
    )


@router.get("/steps", response_model=list[StepOut])
async def list_steps(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    identity: dict[str, Any] = Depends(require_permission("workflow.view"))
):
    """List sub-tasks (steps) for a specific project or all projects."""
    from sqlalchemy import select

    from libs.db.models.core_models import SubTask

    query = select(SubTask)
    if project_id:
        try:
            uid = uuid.UUID(project_id)
            query = query.where(SubTask.project_id == uid)
        except ValueError:
            return []

    res = await db.execute(query)
    subtasks = res.scalars().all()

    items = []
    for st in subtasks:
        status_val = st.status.value if hasattr(st.status, "value") else str(st.status)
        items.append(StepOut(
            id=str(st.id),
            name=st.title,
            action=st.action or "unknown",
            status=status_val.lower(),
            started_at=st.started_at,
            completed_at=st.completed_at,
            retries=0, # Placeholder or add to model if available
            error=getattr(st, "causal_anchor", None) if status_val.lower() in ("error", "failed") else None,
            dependencies=st.dependencies if isinstance(st.dependencies, list) else [],
            output_summary=st.result_summary,
        ))
    return items

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    req: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    identity: dict[str, Any] = Depends(require_permission("workflow.create"))
):
    """
    Manually create a new project/workflow and trigger its execution using the unified runner.
    """
    from libs.db.models.core_models import ProjectSource, TaskPriority
    from libs.db.repositories.repository import ProjectRepository

    # Normalization Guard
    p_val = (req.priority or "MEDIUM").upper().strip()
    mapping = {"YÜKSEK": "HIGH", "ORTA": "MEDIUM", "DÜŞÜK": "LOW", "KRİTİK": "CRITICAL"}
    normalized_priority = mapping.get(p_val, p_val)
    if normalized_priority not in [m.name for m in TaskPriority]:
        normalized_priority = "MEDIUM"

    if _prefer_ephemeral_workflows():
        workflow_id = str(uuid.uuid4())
        _EPHEMERAL_WORKFLOWS[workflow_id] = _build_ephemeral_workflow(workflow_id, req)
        logger.warning("Workflow %s created in memory (ephemeral mode).", workflow_id)
        return {
            "id": workflow_id,
            "status": "queued",
            "dispatch_state": "enqueued",
            "workflow_template": req.workflow_template
        }

    project = await ProjectRepository.create(
        db,
        title=req.title,
        description=req.description,
        workflow_template=req.workflow_template,
        quality_profile=req.quality_profile,
        priority=normalized_priority,
        source=ProjectSource.CONTROL_PLANE
    )
    await db.commit()

    dispatch_state = "enqueued"
    try:
        from services.orchestration.application.job_queue import job_queue
        job = await job_queue.enqueue(
            "run_project",
            project_id=str(project.id),
            title=project.title,
            description=project.description or "",
            workflow_template=project.workflow_template or "default",
            quality_profile=project.quality_profile or "standard",
        )
        project.job_id = job.id
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to dispatch workflow {project.id}: {e}")
        dispatch_state = "deferred"

    return {
        "id": str(project.id),
        "status": "queued" if dispatch_state == "enqueued" else (
            project.status.value.lower() if hasattr(project.status, "value") else str(project.status).lower()
        ),
        "dispatch_state": dispatch_state,
        "workflow_template": project.workflow_template or "default"
    }


@router.get("", response_model=list[ProjectListItem])
async def list_projects(
    response: Response,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all projects/workflows with step summary."""
    from sqlalchemy import func, select

    from libs.db.models.core_models import Project, ProjectStatus, SubTask
    from libs.db.session import AsyncSessionLocal

    if _prefer_ephemeral_workflows() and _EPHEMERAL_WORKFLOWS:
        response.headers["x-total-count"] = str(len(_EPHEMERAL_WORKFLOWS))
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"
        return [
            ProjectListItem(
                id=workflow["id"],
                title=workflow["title"],
                status=workflow["status"],
                workflow_type=workflow["workflow_type"],
                progress_pct=workflow["progress_pct"],
                created_at=workflow["created_at"],
                started_at=workflow["started_at"],
                completed_at=workflow["completed_at"],
                total_steps=workflow["total_steps"],
                completed_steps=workflow["completed_steps"],
                failed_steps=workflow["failed_steps"],
                has_active_workflow=workflow["has_active_workflow"],
            )
            for workflow in reversed(list(_EPHEMERAL_WORKFLOWS.values()))
        ]

    async with AsyncSessionLocal() as db:
        # Get total count for Refine pagination
        count_q = select(func.count(Project.id))
        if status_filter and isinstance(status_filter, str):
            try:
                count_q = count_q.where(Project.status == ProjectStatus(status_filter.upper()))
            except (ValueError, AttributeError):
                pass
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(Project).order_by(Project.created_at.desc()).limit(limit).offset(offset)
        if status_filter and isinstance(status_filter, str):
            try:
                q = q.where(Project.status == ProjectStatus(status_filter.upper()))
            except (ValueError, AttributeError):
                pass  # Unknown status — ignore filter
        projects = (await db.execute(q)).scalars().all()

        items = []
        for p in projects:
            res_counts = await db.execute(
                select(
                    func.count(SubTask.id).label("total"),
                    func.count(SubTask.id).filter(
                        SubTask.status.in_(["COMPLETED", "completed"])
                    ).label("completed"),
                    func.count(SubTask.id).filter(
                        SubTask.status.in_(["ERROR", "error", "FAILED", "failed"])
                    ).label("failed"),
                ).where(SubTask.project_id == p.id)
            )
            row = res_counts.one()
            total, completed, failed = row.total, row.completed, row.failed
            if total == 0:
                total = _workflow_template_step_count(p.workflow_template or "default")
            progress = int((completed / total * 100) if total > 0 else 0)
            p_status = p.status.value if hasattr(p.status, "value") else str(p.status)

            items.append(ProjectListItem(
                id=str(p.id),
                title=p.title,
                status=p_status.lower(),
                workflow_type=p.workflow_template or "default",
                progress_pct=progress,
                created_at=p.created_at,
                started_at=p.started_at,
                completed_at=p.completed_at,
                total_steps=total,
                completed_steps=completed,
                failed_steps=failed,
                has_active_workflow=_is_active_workflow_status(p_status),
            ))
        for workflow in _EPHEMERAL_WORKFLOWS.values():
            items.insert(0, ProjectListItem(
                id=workflow["id"],
                title=workflow["title"],
                status=workflow["status"],
                workflow_type=workflow["workflow_type"],
                progress_pct=workflow["progress_pct"],
                created_at=workflow["created_at"],
                started_at=workflow["started_at"],
                completed_at=workflow["completed_at"],
                total_steps=workflow["total_steps"],
                completed_steps=workflow["completed_steps"],
                failed_steps=workflow["failed_steps"],
                has_active_workflow=workflow["has_active_workflow"],
            ))
        return items
@router.get("/{project_id}", response_model=WorkflowOut)
async def get_workflow(project_id: str):
    """Get full workflow detail with step trace and event history."""
    from sqlalchemy import select

    from libs.db.models.core_models import ApprovalRequest, OperationalIncident
    from libs.db.session import AsyncSessionLocal
    from libs.workflow.persistence import WorkflowPersistence

    if project_id in _EPHEMERAL_WORKFLOWS:
        workflow = _EPHEMERAL_WORKFLOWS[project_id]
        return WorkflowOut(
            id=workflow["id"],
            name=workflow["name"],
            workflow_type=workflow["workflow_type"],
            status=workflow["status"],
            source=workflow["source"],
            steps=workflow["steps"] or _planned_steps_for_template(workflow["workflow_type"]),
            context_keys=workflow["context_keys"],
            payload=workflow["payload"],
            created_at=workflow["created_at"],
            started_at=workflow["started_at"],
            completed_at=workflow["completed_at"],
            final_report=workflow["final_report"],
            history=workflow["history"],
            related_approvals=workflow["related_approvals"],
            related_incidents=workflow["related_incidents"],
        )

    async with AsyncSessionLocal() as db:
        resolved_uid = await _resolve_project_id(db, project_id)

    project, subtasks = await _get_project_with_subtasks(project_id)

    out = _map_workflow(project, subtasks)

    # Map history to UI format (step, msg, timestamp)
    raw_history = await WorkflowPersistence.load_history(str(resolved_uid))
    out.history = [
        {
            "step": str(h["event_type"]).replace("_", " ").title() if h.get("event_type") else "Event",
            "msg": h["payload"].get("msg") or h["payload"].get("details") or f"Event {h['event_type']} processed.",
            "timestamp": h["created_at"].isoformat() if hasattr(h["created_at"], "isoformat") else str(h["created_at"])
        }
        for h in raw_history
    ]

    # Load related governance data (Approvals & Incidents)
    async with AsyncSessionLocal() as db:
        # Fetch Approvals
        app_res = await db.execute(select(ApprovalRequest).where(ApprovalRequest.project_id == resolved_uid))
        out.related_approvals = [
            {
                "id": str(a.id),
                "request_type": a.request_type,
                "status": a.status,
                "reason": a.reason,
                "created_at": a.created_at
            } for a in app_res.scalars().all()
        ]

        # Fetch Incidents
        inc_res = await db.execute(select(OperationalIncident).where(OperationalIncident.project_id == resolved_uid))
        out.related_incidents = [
            {
                "id": str(i.id),
                "incident_type": i.incident_type,
                "status": i.status,
                "severity": i.severity,
                "message": i.message,
                "created_at": i.created_at
            } for i in inc_res.scalars().all()
        ]

    return out


@router.get("/{project_id}/steps/{step_id}/diagnose")
async def diagnose_workflow_step(project_id: str, step_id: str):
    """
    [Phase 4: Metacognition] Returns AI-suggested fix for a failed step.
    """
    from libs.db.session import AsyncSessionLocal
    from libs.workflow.engine import WorkflowEngine
    from libs.workflow.persistence import WorkflowPersistence

    async with AsyncSessionLocal() as db:
        resolved_uid = await _resolve_project_id(db, project_id)

    persistence = WorkflowPersistence()
    instance = await persistence.load_instance(str(resolved_uid))
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")

    engine = WorkflowEngine()
    suggestion = await engine.suggest_fix(instance, step_id)
    return suggestion

@router.post("/{project_id}/replay", response_model=dict[str, Any])
async def replay_workflow(
    project_id: str,
    req: ReplayRequest,
    identity: dict[str, Any] = Depends(require_permission("workflow.replay"))
):
    """Trigger a durable replay of a workflow with hardening & audit trail."""
    from libs.db.session import AsyncSessionLocal
    from libs.workflow.engine import WorkflowEngine
    from libs.workflow.persistence import WorkflowPersistence

    persistence = WorkflowPersistence()

    async with AsyncSessionLocal() as db:
        resolved_uid = await _resolve_project_id(db, project_id)

    # 1. Load instance and check concurrency
    instance = await persistence.load_instance(str(resolved_uid))
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")

    status_str = instance.status.value if hasattr(instance.status, "value") else str(instance.status)
    if status_str.lower() in ["running", "replaying"]:
        raise HTTPException(
            status_code=409,
            detail=f"Workflow is currently {status_str}. Stop or wait for completion before replay."
        )

    # 2. Basic Override Validation
    if req.mode == "with_override" and not req.overrides:
        raise HTTPException(status_code=400, detail="Overrides required for 'with_override' mode.")

    # 3. Log Audit Event before starting
    await persistence.save_event(
        project_id,
        "replay_initiated",
        step_id=req.from_step,
        payload={
            "mode": req.mode,
            "reason": req.reason,
            "operator_id": str(identity.get("id", "system")),
            "operator_name": identity.get("name", "Unknown"),
            "overrides_keys": list(req.overrides.keys()) if req.overrides else []
        }
    )

    # 4. Trigger Engine
    engine = WorkflowEngine()
    await engine.replay(
        instance,
        from_step_id=req.from_step,
        mode=req.mode,
        overrides=req.overrides,
        operator_id=req.operator_id,
        reason=req.reason
    )

    return {
        "status": "success",
        "message": "Durable replay sequence authorized and initiated.",
        "project_id": project_id,
        "audit_id": req.operator_id
    }


@router.post("/{project_id}/cancel")
async def cancel_workflow(project_id: str):
    """Cancel a running or pending workflow by updating status and notifying the queue."""
    from sqlalchemy import select

    from libs.db.models.core_models import Project, ProjectStatus
    from libs.db.repositories.repository import ProjectRepository
    from libs.db.session import AsyncSessionLocal
    from services.orchestration.application.job_queue import job_queue

    if project_id in _EPHEMERAL_WORKFLOWS:
        _EPHEMERAL_WORKFLOWS[project_id]["status"] = "cancelled"
        return {"message": "Ephemeral workflow cancelled", "project_id": project_id}

    async with AsyncSessionLocal() as db:
        uid = await _resolve_project_id(db, project_id)
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.CANCELLED,
            cancelled_at=datetime.now(UTC),
            cancelled_by="control_plane",
        )
        await db.commit()

        # Request cancellation from the job queue if active
        try:
            if hasattr(job_queue, "request_cancel"):
                await job_queue.request_cancel(str(project.id))
        except Exception as e:
            logger.warning(f"Failed to request job cancellation for {project.id}: {e}")

    return {"message": "Workflow cancelled and queue notified.", "project_id": project_id}


@router.post("/{project_id}/reassign")
async def reassign_workflow(
    project_id: str,
    req: ReassignRequest,
    identity: dict[str, Any] = Depends(require_permission("workflow.approve"))
):
    """Re-queue a cancelled/failed workflow so operators can assign it again."""
    from sqlalchemy import select, update

    from libs.db.models.core_models import Project, ProjectStatus, SubTask
    from libs.db.session import AsyncSessionLocal
    from libs.workflow.persistence import WorkflowPersistence
    from services.orchestration.application.job_queue import job_queue

    if project_id in _EPHEMERAL_WORKFLOWS:
        workflow = _EPHEMERAL_WORKFLOWS[project_id]
        current_status = workflow.get("status")
        if _is_active_workflow_status(current_status):
            raise HTTPException(status_code=409, detail=f"Workflow is already active (status: {current_status})")
        if not _is_reassignable_workflow_status(current_status):
            raise HTTPException(status_code=409, detail=f"Workflow status is not reassignable (status: {current_status})")
        workflow["status"] = "queued"
        workflow["progress_pct"] = 0
        workflow["has_active_workflow"] = True
        return {
            "status": "success",
            "message": "Ephemeral workflow re-queued.",
            "project_id": project_id,
            "dispatch_state": "enqueued",
            "previous_status": current_status,
            "reset_steps": False,
        }

    persistence = WorkflowPersistence()
    dispatch_state = "enqueued"
    reset_step_count = 0
    previous_status = ""

    async with AsyncSessionLocal() as db:
        uid = await _resolve_project_id(db, project_id)
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        previous_status = project.status.value if hasattr(project.status, "value") else str(project.status)
        if _is_active_workflow_status(previous_status):
            raise HTTPException(status_code=409, detail=f"Workflow is already active (status: {previous_status})")
        if not _is_reassignable_workflow_status(previous_status):
            raise HTTPException(status_code=409, detail=f"Workflow status is not reassignable (status: {previous_status})")

        now = datetime.now(UTC)
        project_title = project.title
        project_description = project.description or ""
        project_template = project.workflow_template or "default"
        project_quality = project.quality_profile or "standard"
        notes = f"[REASSIGNED BY {identity.get('name', req.operator_id)}] {req.reason}"
        update_values = {
            "status": ProjectStatus.QUEUED,
            "progress_pct": 0,
            "error_detail": "",
            "cancelled_at": None,
            "cancelled_by": None,
            "completed_at": None,
            "retry_count": Project.retry_count + 1,
            "notes": notes,
            "updated_at": now,
        }
        if req.assigned_agent:
            update_values["assigned_agent"] = req.assigned_agent

        await db.execute(update(Project).where(Project.id == uid).values(**update_values))

        if req.reset_steps:
            reset_stmt = update(SubTask).where(SubTask.project_id == uid)
            if req.preserve_completed_steps:
                reset_stmt = reset_stmt.where(SubTask.status != ProjectStatus.COMPLETED)
            result = await db.execute(
                reset_stmt.values(
                    status=ProjectStatus.PENDING,
                    attempts=0,
                    result="",
                    completed_at=None,
                    causal_anchor="",
                    updated_at=now,
                )
            )
            reset_step_count = result.rowcount or 0

        await db.commit()

        await persistence.save_event(
            str(uid),
            "workflow_reassigned",
            payload={
                "operator_id": req.operator_id,
                "operator_name": identity.get("name", "Unknown"),
                "previous_status": previous_status,
                "reason": req.reason,
                "reset_steps": req.reset_steps,
                "preserve_completed_steps": req.preserve_completed_steps,
                "reset_step_count": reset_step_count,
                "assigned_agent": req.assigned_agent,
                "timestamp": now.isoformat(),
            },
        )

        try:
            job = await asyncio.wait_for(
                job_queue.enqueue(
                    "run_project",
                    project_id=str(uid),
                    title=project_title,
                    description=project_description,
                    workflow_template=project_template,
                    quality_profile=project_quality,
                ),
                timeout=5,
            )
            await db.execute(update(Project).where(Project.id == uid).values(job_id=job.id))
            await db.commit()
        except TimeoutError:
            dispatch_state = "deferred"
            logger.warning("[WorkflowReassign] enqueue timeout for project=%s; workflow remains queued.", project_id)
        except Exception as e:
            dispatch_state = "deferred"
            logger.error("[WorkflowReassign] enqueue failed for project=%s: %s", project_id, e)

    return {
        "status": "success",
        "message": "Workflow re-assigned and re-queued.",
        "project_id": project_id,
        "dispatch_state": dispatch_state,
        "previous_status": previous_status,
        "reset_steps": req.reset_steps,
        "reset_step_count": reset_step_count,
    }


@router.post("/{project_id}/approve")
async def approve_workflow(
    project_id: str,
    req: ApprovalRequest,
    identity: dict[str, Any] = Depends(require_permission("workflow.approve"))
):
    """Approve a workflow pending manual review with audit trail."""
    from sqlalchemy import select

    from libs.db.models.core_models import Project, ProjectStatus
    from libs.db.repositories.repository import ProjectRepository
    from libs.db.session import AsyncSessionLocal
    from libs.workflow.persistence import WorkflowPersistence

    persistence = WorkflowPersistence()

    async with AsyncSessionLocal() as db:
        uid = await _resolve_project_id(db, project_id)
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        p_status = project.status.value if hasattr(project.status, "value") else str(project.status)
        if p_status.lower() not in ("pending_approval", "waiting_approval", "pending", "queued"):
            raise HTTPException(status_code=409, detail=f"Project is not pending approval (status: {p_status})")

        # Hardening: Save to Workflow Audit Trail
        await persistence.save_event(
            project_id,
            "workflow_approved",
            payload={
                "operator_id": str(identity["id"]),
                "operator_name": identity["name"],
                "notes": req.notes,
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.QUEUED,
            notes=f"[APPROVED BY {identity['name']}] {req.notes}",
            review_required=False,
        )
        # Faz 13.04: Reset waiting steps to PENDING to break deadlock on resumption
        from sqlalchemy import update

        from libs.db.models.core_models import ProjectStatus, SubTask
        await db.execute(
            update(SubTask)
            .where(SubTask.project_id == uid, SubTask.status == "WAITING")
            .values(status=ProjectStatus.PENDING)
        )
        await db.commit()

    # Dispatch to standardized job queue to resume execution.
    # Guard against queue backend stalls so approval endpoint does not hang.
    from services.orchestration.application.job_queue import job_queue
    dispatch_state = "enqueued"
    try:
        await asyncio.wait_for(
            job_queue.enqueue(
                "run_project",
                project_id=project_id,
                title=project.title,
                description=project.description or "",
                workflow_template=project.workflow_template or "default",
                quality_profile=project.quality_profile or "standard",
            ),
            timeout=5,
        )
    except TimeoutError:
        dispatch_state = "deferred"
        logger.warning("[WorkflowApprove] enqueue timeout for project=%s; workflow remains queued.", project_id)
    except Exception as e:
        dispatch_state = "deferred"
        logger.error("[WorkflowApprove] enqueue failed for project=%s: %s", project_id, e)

    return {
        "status": "success",
        "msg": "Workflow approved and re-queued",
        "message": "Workflow approved and re-queued",
        "project_id": project_id,
        "dispatch_state": dispatch_state,
    }


# Replaced by merged version above


@router.get("/stats/summary")
async def workflow_stats():
    """Aggregate stats for control plane header metrics including systemic anomalies."""
    from sqlalchemy import func, select

    from libs.db.models.core_models import Project
    from libs.db.models.learning_models import ErrorFingerprint
    from libs.db.session import AsyncSessionLocal

    if _prefer_ephemeral_workflows() and _EPHEMERAL_WORKFLOWS:
        ephemeral_total = len(_EPHEMERAL_WORKFLOWS)
        return {
            "total": ephemeral_total,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "pending": ephemeral_total,
            "pending_approval": 0,
            "success_rate_pct": 0.0,
            "systemic_anomalies": 0,
            "pending_improvements": 0,
            "status_breakdown": {"queued": ephemeral_total},
        }

    async with AsyncSessionLocal() as db:
        # 1. Project stats
        result = await db.execute(
            select(
                Project.status,
                func.count(Project.id).label("cnt")
            ).group_by(Project.status)
        )
        rows = result.all()

        active_failed_count = (
            await db.execute(
                select(func.count(Project.id)).where(
                    Project.status.in_(["ERROR", "error", "FAILED", "failed"]),
                    Project.completed_at.is_(None),
                )
            )
        ).scalar() or 0

        historical_failed_count = (
            await db.execute(
                select(func.count(Project.id)).where(
                    Project.status.in_(["ERROR", "error", "FAILED", "failed"]),
                    Project.completed_at.is_not(None),
                )
            )
        ).scalar() or 0

        # 2. Systemic anomalies count (Error Fingerprints)
        f_count = (await db.execute(select(func.count(ErrorFingerprint.id)).where(ErrorFingerprint.is_active == True))).scalar() or 0

        # 3. Pending Improvements count
        from libs.db.models.core_models import SystemImprovement
        i_count = (await db.execute(select(func.count(SystemImprovement.id)).where(SystemImprovement.status == "pending"))).scalar() or 0

    counts: dict[str, int] = {}
    for row in rows:
        s = row.status.value if hasattr(row.status, "value") else str(row.status)
        counts[s.lower()] = row.cnt

    total = sum(counts.values())
    running = counts.get("running", 0)
    completed = counts.get("completed", 0) + counts.get("partial_complete", 0)
    # Header metrics should describe current operational failures. Historical
    # completed ERROR records are exposed separately so old smoke failures do
    # not keep the live UI in a degraded-looking state.
    failed = active_failed_count + f_count + i_count
    pending = counts.get("pending", 0) + counts.get("queued", 0)
    pending_approval = counts.get("pending_approval", 0)

    success_rate = round(completed / max(completed + failed, 1) * 100, 1)

    if _EPHEMERAL_WORKFLOWS:
        ephemeral_total = len(_EPHEMERAL_WORKFLOWS)
        total += ephemeral_total
        pending += ephemeral_total
        counts["queued"] = counts.get("queued", 0) + ephemeral_total

    return {
        "total": total,
        "running": running,
        "completed": completed,
        "failed": failed,
        "historical_failed": historical_failed_count,
        "pending": pending,
        "pending_approval": pending_approval,
        "success_rate_pct": success_rate,
        "systemic_anomalies": f_count,
        "pending_improvements": i_count,
        "status_breakdown": counts,
    }





@router.get("/analytics/failure-clusters", tags=["Analytics"])
async def get_failure_clusters():
    """Group recent workflow failures by error pattern."""
    import re
    from collections import Counter

    from sqlalchemy import select

    from libs.db.models.core_models import WorkflowEvent
    from libs.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get last 100 step_failed events
        q = select(WorkflowEvent).where(WorkflowEvent.event_type == "step_failed").order_by(WorkflowEvent.created_at.desc()).limit(100)
        res = await db.execute(q)
        events = res.scalars().all()

    clusters = []
    error_messages = []

    for e in events:
        msg = e.payload.get("error", "Unknown error")
        # Sanitize message: remove IDs and paths to group similar errors
        msg = re.sub(r'0x[a-fA-F0-0]+', 'ID', msg)
        msg = re.sub(r'/[^ ]+', '/PATH', msg)
        error_messages.append(msg)

    counts = Counter(error_messages)

    for msg, count in counts.items():
        clusters.append({
            "pattern": msg,
            "count": count,
            "severity": "high" if count > 5 else "medium"
        })

    return sorted(clusters, key=lambda x: x["count"], reverse=True)
