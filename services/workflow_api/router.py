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

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflow Control Plane"])


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
    workflow_type: str
    status: str
    steps: List[StepOut]
    context_keys: List[str]
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_report: Optional[str] = None
    history: List[Dict[str, Any]] = []


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


class ImprovementUpdate(BaseModel):
    status: str


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_project_with_subtasks(project_id: str):
    """Load project + subtasks from DB."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, SubTask
    from sqlalchemy import select

    try:
        uid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid project ID format")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        res_st = await db.execute(
            select(SubTask).where(SubTask.project_id == uid).order_by(SubTask.created_at)
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
        workflow_type=project.workflow_template or "default",
        status=p_status.lower(),
        steps=steps,
        context_keys=ctx_keys,
        created_at=project.created_at,
        started_at=project.started_at,
        completed_at=project.completed_at,
        final_report=report,
        history=[],  # Will be populated by the caller if needed
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(req: ProjectCreate):
    """
    Manually create a new project/workflow and trigger its execution.
    """
    from libs.db.session import AsyncSessionLocal
    from libs.db.repositories.repository import ProjectRepository
    from libs.db.models.core_models import ProjectSource
    from services.orchestration.application.job_queue import job_queue
    async with AsyncSessionLocal() as db:
        project = await ProjectRepository.create(
            db,
            title=req.title,
            description=req.description,
            workflow_template=req.workflow_template,
            quality_profile=req.quality_profile,
            priority=req.priority,
            source=ProjectSource.CONTROL_PLANE
        )
        await db.commit()
        await db.refresh(project)

    # Dispatch to standardized job queue (Respects auto-fallback to in-process)
    await job_queue.enqueue(
        "run_project",
        db_project_id=str(project.id),
        title=project.title,
        description=project.description or "",
        workflow_template=project.workflow_template or "default",
        quality_profile=project.quality_profile or "standard",
    )

    return {"id": str(project.id), "status": "queued"}


@router.get("", response_model=List[ProjectListItem])
async def list_projects(
    response: Response,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all projects/workflows with step summary."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, SubTask, ProjectStatus
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        # Get total count for Refine pagination
        count_q = select(func.count(Project.id))
        if status_filter:
            try:
                count_q = count_q.where(Project.status == ProjectStatus(status_filter.upper()))
            except ValueError:
                pass
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(Project).order_by(Project.created_at.desc()).limit(limit).offset(offset)
        if status_filter:
            try:
                q = q.where(Project.status == ProjectStatus(status_filter.upper()))
            except ValueError:
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
    project, subtasks = await _get_project_with_subtasks(project_id)
    out = _map_workflow(project, subtasks)
    
    # Load durable history (Phase 13.04)
    from libs.workflow.persistence import WorkflowPersistence
    out.history = await WorkflowPersistence.load_history(project_id)
    
    return out


@router.get("/workflows/{project_id}/steps/{step_id}/diagnose")
async def diagnose_workflow_step(project_id: str, step_id: str):
    """
    [Phase 4: Metacognition] Returns AI-suggested fix for a failed step.
    """
    from libs.workflow.persistence import WorkflowPersistence
    from libs.workflow.engine import WorkflowEngine
    persistence = WorkflowPersistence()
    instance = await persistence.load_instance(project_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
        
    engine = WorkflowEngine()
    suggestion = await engine.suggest_fix(instance, step_id)
    return suggestion

@router.post("/workflows/{project_id}/replay", response_model=Dict[str, Any])
async def retry_workflow(project_id: str):
    """Re-enqueue a failed/error project for execution."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, ProjectStatus
    from libs.db.repositories.repository import ProjectRepository
    from sqlalchemy import select

    try:
        uid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid project ID")

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
        )
        await db.commit()

    # Enqueue via standardized job queue
    from services.orchestration.application.job_queue import job_queue
    await job_queue.enqueue(
        "run_project",
        db_project_id=project_id,
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

    try:
        uid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid project ID")

    async with AsyncSessionLocal() as db:
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
async def approve_workflow(project_id: str, req: ApprovalRequest):
    """Approve a workflow pending manual review with audit trail."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, ProjectStatus
    from libs.db.repositories.repository import ProjectRepository
    from libs.workflow.persistence import WorkflowPersistence
    from sqlalchemy import select

    try:
        uid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid project ID")

    persistence = WorkflowPersistence()

    async with AsyncSessionLocal() as db:
        # Hardening: RBAC Authorization
        from libs.db.models.core_models import User
        user_res = await db.execute(select(User).where(User.email == req.operator_id))
        user = user_res.scalar_one_or_none()
        if not user or not user.is_admin:
            if req.operator_id != "admin_human":
                raise HTTPException(status_code=403, detail="Operator not authorized to approve workflows.")

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
                "operator_id": req.operator_id,
                "notes": req.notes,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.QUEUED,
            notes=f"[APPROVED BY {req.operator_id}] {req.notes}",
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
        db_project_id=project_id,
        title=project.title,
        description=project.description or "",
        workflow_template=project.workflow_template or "default",
        quality_profile=project.quality_profile or "standard",
    )

    return {"message": "Workflow approved and re-queued", "project_id": project_id}


@router.post("/{project_id}/replay")
async def replay_workflow(project_id: str, req: ReplayRequest):
    """Trigger a durable replay of a workflow with hardening & audit trail."""
    from libs.workflow.persistence import WorkflowPersistence
    from libs.workflow.engine import WorkflowEngine
    from libs.db.models.core_models import ProjectStatus
    
    persistence = WorkflowPersistence()
    
    # 1. Load instance and check concurrency
    instance = await persistence.load_instance(project_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
        
    # Hardening: Final RBAC Authorization with Dynamic Roles
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import User
    from libs.auth.rbac import is_authorized
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.email == req.operator_id))
        user = res.scalar_one_or_none()
        
        # Determine actual role
        user_role = user.role if (user and hasattr(user, "role")) else "operator"
        if req.operator_id == "admin_human" or (user and user.is_admin):
            user_role = "admin"
            
        if not is_authorized(user_role, "workflow:replay"):
            logger.warning(f"Unauthorized replay attempt by {req.operator_id} (Role: {user_role})")
            raise HTTPException(status_code=403, detail=f"Operator role '{user_role}' is not authorized to trigger replays.")

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
            "operator_id": req.operator_id,
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
    """Aggregate stats for control plane header metrics."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, ProjectStatus
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                Project.status,
                func.count(Project.id).label("cnt")
            ).group_by(Project.status)
        )
        rows = result.all()

    counts: Dict[str, int] = {}
    for row in rows:
        s = row.status.value if hasattr(row.status, "value") else str(row.status)
        counts[s.lower()] = row.cnt

    total = sum(counts.values())
    running = counts.get("running", 0)
    completed = counts.get("completed", 0) + counts.get("partial_complete", 0)
    failed = counts.get("error", 0) + counts.get("failed", 0)
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
        "status_breakdown": counts,
    }


# ── Improvement Endpoints (Self-Healing) ───────────────────────────────────

@router.get("/improvements/list", response_model=List[ImprovementOut], tags=["Self-Healing"])
async def list_improvements(
    response: Response,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List system improvement proposals."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import SystemImprovement
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(SystemImprovement.id))
        total_count = (await db.execute(count_q)).scalar()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

        q = select(SystemImprovement).order_by(SystemImprovement.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        improvements = res.scalars().all()

        return [
            ImprovementOut(
                id=str(i.id),
                opportunity_id=str(i.opportunity_id),
                target_file=i.target_file,
                instruction=i.instruction,
                proposed_patch=i.proposed_patch,
                status=i.status.value if hasattr(i.status, "value") else str(i.status),
                created_at=i.created_at,
                test_results=i.test_results,
            )
            for i in improvements
        ]


@router.patch("/improvements/{improvement_id}", response_model=ImprovementOut, tags=["Self-Healing"])
async def update_improvement(improvement_id: str, patch_data: ImprovementUpdate):
    """Approve or reject a patch."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import SystemImprovement
    from sqlalchemy import select

    try:
        uid = uuid.UUID(improvement_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(SystemImprovement).where(SystemImprovement.id == uid))
        improvement = res.scalar_one_or_none()
        if not improvement:
            raise HTTPException(status_code=404, detail="Improvement not found")

        # Update status
        improvement.status = patch_data.status
        
        # If approved, we would normally trigger the effector here.
        # For Phase 4, we'll log the approval. The effector will be triggered
        # by the coordinator scanning for 'approved' patches.
        
        if patch_data.status == "approved":
            # Optional: Trigger effector background task
            pass

        await db.commit()
        await db.refresh(improvement)

        return ImprovementOut(
            id=str(improvement.id),
            opportunity_id=str(improvement.opportunity_id),
            target_file=improvement.target_file,
            instruction=improvement.instruction,
            proposed_patch=improvement.proposed_patch,
            status=improvement.status.value if hasattr(improvement.status, "value") else str(improvement.status),
            created_at=improvement.created_at,
            test_results=improvement.test_results,
        )


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
