"""
Workflow Control Plane API — Phase 13.04
Exposes workflow runs, step details, retry/replay, and approval controls.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from libs.db.session import get_db
from services.auth.jwt_auth import require_permission

router = APIRouter(tags=["Workflow Control Plane"])


# ── Response Schemas ──────────────────────────────────────────────────────────

class StepOut(BaseModel):
    id: str
    name: str
    action: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    dependencies: List[str] = []
    output_summary: Optional[str] = None


class WorkflowOut(BaseModel):
    id: str
    name: str
    workflow_type: str
    status: str
    source: str
    steps: List[StepOut]
    context_keys: List[str]
    payload: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_report: Optional[str] = None
    history: List[Dict[str, Any]] = []
    related_approvals: List[Dict[str, Any]] = []
    related_incidents: List[Dict[str, Any]] = []


class ProjectListItem(BaseModel):
    id: str
    title: str
    status: str
    workflow_type: str
    progress_pct: int
    created_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
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
    overrides: Optional[Dict[str, Any]] = None
    reason: str               # Audit requirement: why is this being replayed?
    operator_id: str          # Audit requirement: who is replaying?

class ApprovalRequest(BaseModel):
    operator_id: str
    notes: str = ""


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
    test_results: Optional[Dict[str, Any]] = None





# ── Helpers ───────────────────────────────────────────────────────────────────

# ── Helpers ───────────────────────────────────────────────────────────────────
async def _resolve_project_id(db, project_id: str):
    """
    Resolves a full UUID or short-ID prefix to a validated Project.id (uuid.UUID).
    """
    from libs.db.models.core_models import Project
    from sqlalchemy import select, cast, String, func
    
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
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, SubTask
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        resolved_uid = await _resolve_project_id(db, project_id)
        
        res = await db.execute(select(Project).where(Project.id == resolved_uid))
        project = res.scalar_one_or_none()
        
        res_st = await db.execute(
            select(SubTask).where(SubTask.project_id == resolved_uid).order_by(SubTask.created_at)
        )
        subtasks = res_st.scalars().all()
        return project, subtasks


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


@router.get("/steps", response_model=List[StepOut])
async def list_steps(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("workflow.view"))
):
    """List sub-tasks (steps) for a specific project or all projects."""
    from libs.db.models.core_models import SubTask
    from sqlalchemy import select

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
    identity: Dict[str, Any] = Depends(require_permission("workflow.create"))
):
    """
    Manually create a new project/workflow and trigger its execution.
    """
    from libs.db.session import AsyncSessionLocal
    from libs.db.repositories.repository import ProjectRepository
    from libs.db.models.core_models import ProjectSource, TaskPriority
    from services.orchestration.application.job_queue import job_queue

    # Normalization Guard: Protect against case-insensitive and localized inputs
    p_val = (req.priority or "MEDIUM").upper().strip()
    mapping = {
        "YÜKSEK": "HIGH", "YUKSEK": "HIGH",
        "ORTA": "MEDIUM", "DÜŞÜK": "LOW", "DUSUK": "LOW",
        "KRİTİK": "CRITICAL", "KRITIK": "CRITICAL"
    }
    normalized_priority = mapping.get(p_val, p_val)
    
    # Ensure it's a valid enum member name
    if normalized_priority not in [m.name for m in TaskPriority]:
        normalized_priority = "MEDIUM"

    async with AsyncSessionLocal() as db:
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
        await db.refresh(project)

    # Dispatch to standardized job queue (Respects auto-fallback to in-process)
    await job_queue.enqueue(
        "run_project",
        project_id=str(project.id),
        title=project.title,
        description=project.description or "",
        workflow_template=project.workflow_template or "default",
        quality_profile=project.quality_profile or "standard",
    )

    return {"id": str(project.id), "status": "queued"}


@router.get("", response_model=List[ProjectListItem])
async def list_projects(
    response: Response,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all projects/workflows with step summary."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, SubTask, ProjectStatus
    from sqlalchemy import select, func

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
                has_active_workflow=p_status.lower() in ("running", "pending", "resuming"),
            ))
        return items
@router.get("/{project_id}", response_model=WorkflowOut)
async def get_workflow(project_id: str):
    """Get full workflow detail with step trace and event history."""
    from libs.workflow.persistence import WorkflowPersistence
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import ApprovalRequest, OperationalIncident
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        resolved_uid = await _resolve_project_id(db, project_id)

    project, subtasks = await _get_project_with_subtasks(project_id)

    out = _map_workflow(project, subtasks)
    
    # Map history to UI format (step, msg, timestamp)
    raw_history = await WorkflowPersistence.load_history(str(resolved_uid))
    out.history = [
        {
            "step": h["event_type"].replace("_", " ").title(),
            "msg": h["payload"].get("msg") or h["payload"].get("details") or f"Event {h['event_type']} processed.",
            "timestamp": h["created_at"].isoformat()
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
    from libs.workflow.persistence import WorkflowPersistence
    from libs.workflow.engine import WorkflowEngine

    async with AsyncSessionLocal() as db:
        resolved_uid = await _resolve_project_id(db, project_id)
        
    persistence = WorkflowPersistence()
    instance = await persistence.load_instance(str(resolved_uid))
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
        
    engine = WorkflowEngine()
    suggestion = await engine.suggest_fix(instance, step_id)
    return suggestion

@router.post("/{project_id}/replay", response_model=Dict[str, Any])
async def retry_workflow(
    project_id: str,
    identity: Dict[str, Any] = Depends(require_permission("workflow.retry"))
):
    """Re-enqueue a failed/error project for execution."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, ProjectStatus
    from libs.db.repositories.repository import ProjectRepository
    from sqlalchemy import select

    try:
        uid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found (Invalid ID format)")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        p_status = project.status.value if hasattr(project.status, "value") else str(project.status)
        if p_status.lower() not in ("error", "failed", "cancelled", "completed", "partial_complete"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot retry project in status '{p_status}'. Must be error/failed/completed."
            )

        # Reset project status
        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.QUEUED,
            error_detail="",
            retry_count=project.retry_count + 1,
            notes=f"[RETRY BY {identity['name']}]"
        )
        await db.commit()

    # Enqueue via standardized job queue
    from services.orchestration.application.job_queue import job_queue
    await job_queue.enqueue(
        "run_project",
        project_id=project_id,
        title=project.title,
        description=project.description or "",
        workflow_template=project.workflow_template or "default",
        quality_profile=project.quality_profile or "standard",
    )
    return RetryResponse(message="Workflow re-queued successfully", task_id=project_id)


@router.post("/{project_id}/cancel")
async def cancel_workflow(project_id: str):
    """Cancel a running or pending workflow."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, ProjectStatus
    from libs.db.repositories.repository import ProjectRepository
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        uid = await _resolve_project_id(db, project_id)
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.CANCELLED,
            cancelled_at=datetime.now(timezone.utc),
            cancelled_by="control_plane",
        )
        await db.commit()

    return {"message": "Workflow cancelled", "project_id": project_id}


@router.post("/{project_id}/approve")
async def approve_workflow(
    project_id: str, 
    req: ApprovalRequest,
    identity: Dict[str, Any] = Depends(require_permission("workflow.approve"))
):
    """Approve a workflow pending manual review with audit trail."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, ProjectStatus
    from libs.db.repositories.repository import ProjectRepository
    from libs.workflow.persistence import WorkflowPersistence
    from sqlalchemy import select

    persistence = WorkflowPersistence()

    async with AsyncSessionLocal() as db:
        uid = await _resolve_project_id(db, project_id)
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        p_status = project.status.value if hasattr(project.status, "value") else str(project.status)
        if p_status.lower() not in ("pending_approval", "waiting_approval"):
            raise HTTPException(status_code=409, detail=f"Project is not pending approval (status: {p_status})")

        # Hardening: Save to Workflow Audit Trail
        await persistence.save_event(
            project_id, 
            "workflow_approved", 
            payload={
                "operator_id": str(identity["id"]),
                "operator_name": identity["name"],
                "notes": req.notes,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.QUEUED,
            notes=f"[APPROVED BY {identity['name']}] {req.notes}",
            review_required=False,
        )
        # Faz 13.04: Reset waiting steps to PENDING to break deadlock on resumption
        from libs.db.models.core_models import SubTask, ProjectStatus
        from sqlalchemy import update
        await db.execute(
            update(SubTask)
            .where(SubTask.project_id == uid, SubTask.status == "WAITING")
            .values(status=ProjectStatus.PENDING)
        )
        await db.commit()

    # Dispatch to standardized job queue to resume execution
    from services.orchestration.application.job_queue import job_queue
    await job_queue.enqueue(
        "run_project",
        project_id=project_id,
        title=project.title,
        description=project.description or "",
        workflow_template=project.workflow_template or "default",
        quality_profile=project.quality_profile or "standard",
    )

    return {
        "status": "success",
        "msg": "Workflow approved and re-queued",
        "message": "Workflow approved and re-queued", 
        "project_id": project_id
    }


@router.post("/{project_id}/replay")
async def replay_workflow(
    project_id: str, 
    req: ReplayRequest,
    identity: Dict[str, Any] = Depends(require_permission("workflow.replay"))
):
    """Trigger a durable replay of a workflow with hardening & audit trail."""
    from libs.db.session import AsyncSessionLocal
    from libs.workflow.persistence import WorkflowPersistence
    from libs.workflow.engine import WorkflowEngine
    from libs.db.models.core_models import ProjectStatus
    
    persistence = WorkflowPersistence()
    
    async with AsyncSessionLocal() as db:
        resolved_uid = await _resolve_project_id(db, project_id)
        
    # 1. Load instance and check concurrency
    instance = await persistence.load_instance(str(resolved_uid))
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
        
    from libs.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        # Permission verified by Depends
        pass

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
            "operator_id": str(identity["id"]),
            "operator_name": identity["name"],
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


@router.get("/stats/summary")
async def workflow_stats():
    """Aggregate stats for control plane header metrics including systemic anomalies."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, ProjectStatus
    from libs.db.models.learning_models import ErrorFingerprint
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        # 1. Project stats
        result = await db.execute(
            select(
                Project.status,
                func.count(Project.id).label("cnt")
            ).group_by(Project.status)
        )
        rows = result.all()
        
        # 2. Systemic anomalies count (Error Fingerprints)
        f_count = (await db.execute(select(func.count(ErrorFingerprint.id)).where(ErrorFingerprint.is_active == True))).scalar() or 0
        
        # 3. Pending Improvements count
        from libs.db.models.core_models import SystemImprovement
        i_count = (await db.execute(select(func.count(SystemImprovement.id)).where(SystemImprovement.status == "pending"))).scalar() or 0

    counts: Dict[str, int] = {}
    for row in rows:
        s = row.status.value if hasattr(row.status, "value") else str(row.status)
        counts[s.lower()] = row.cnt

    total = sum(counts.values())
    running = counts.get("running", 0)
    completed = counts.get("completed", 0) + counts.get("partial_complete", 0)
    # Add systemic anomalies and pending patches to failed count to ensure visibility in the header
    failed = counts.get("error", 0) + counts.get("failed", 0) + f_count + i_count
    pending = counts.get("pending", 0) + counts.get("queued", 0)
    pending_approval = counts.get("pending_approval", 0)

    success_rate = round(completed / max(completed + failed, 1) * 100, 1)

    return {
        "total": total,
        "running": running,
        "completed": completed,
        "failed": failed,
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
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import WorkflowEvent
    from sqlalchemy import select
    import re
    from collections import Counter

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
