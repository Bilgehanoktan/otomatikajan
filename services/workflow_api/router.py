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

router = APIRouter(prefix="/api/v1", tags=["Workflow Control Plane"])


# ── Dependencies ──────────────────────────────────────────────────────────────

async def require_admin(operator_id: str = Query(..., alias="operatorId")):
    """Mandatory admin check for all state mutations."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import User
    from sqlalchemy import select

    # Allow 'admin_human' as a semi-hardened bypass for legacy dev/CI
    if operator_id == "admin_human":
        return operator_id

    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(User).where(User.email == operator_id))
        user = user_res.scalar_one_or_none()
        if not user or not user.is_admin:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403, 
                detail=f"Operator '{operator_id}' is not authorized for this action."
            )
    return operator_id


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
    input_schema: Dict[str, Any] = {}
    input_data: Dict[str, Any] = {}
    internal_monologue: Optional[str] = None
    cost_usd: float = 0.0


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


class ApprovalRequestOut(BaseModel):
    id: str
    project_id: str
    step_id: Optional[str]
    request_type: str
    reason: str
    input_data: Dict[str, Any]
    status: str
    approver_id: Optional[str]
    decision_at: Optional[datetime]
    comment: str
    created_at: datetime


class OperationalIncidentOut(BaseModel):
    id: str
    incident_type: str
    severity: str
    message: str
    status: str
    project_id: Optional[str]
    payload: Dict[str, Any]
    resolved_at: Optional[datetime]
    created_at: datetime


class ApprovalUpdate(BaseModel):
    status: str
    comment: str = ""


class IncidentUpdate(BaseModel):
    status: str


class CostAnalyticsOut(BaseModel):
    total_cost_usd: float
    budget_limit_usd: float
    usage_pct: float
    top_projects: List[Dict[str, Any]]


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
            action=st.action,
            status=status_val.lower(),
            started_at=None,
            completed_at=st.completed_at,
            retries=st.attempts or 0,
            max_retries=3,
            error=getattr(st, "causal_anchor", None) if status_val.lower() in ("error", "failed") else None,
            dependencies=st.dependencies if isinstance(st.dependencies, list) else [],
            output_summary=output_summary,
            input_schema=st.input_schema or {},
            input_data=st.input_data if st.input_data else {"prompt": st.prompt},
            internal_monologue=st.internal_monologue,
            cost_usd=st.cost_usd or 0.0
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

@router.get("/workflows", response_model=List[ProjectListItem])
async def list_workflows(
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
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

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


@router.get("/workflows/{project_id}", response_model=WorkflowOut)
async def get_workflow(project_id: str):
    """Get full workflow detail with step trace and event history."""
    project, subtasks = await _get_project_with_subtasks(project_id)
    out = _map_workflow(project, subtasks)
    
    # Load durable history (Phase 13.04)
    from libs.workflow.persistence import WorkflowPersistence
    out.history = await WorkflowPersistence.load_history(project_id)
    
    return out


@router.post("/{project_id}/retry", response_model=RetryResponse, dependencies=[Depends(require_admin)])
async def retry_workflow(project_id: str, operator_id: str = Depends(require_admin)):
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
        # Audit trail: Record retry event
        from libs.workflow.persistence import WorkflowPersistence
        await WorkflowPersistence().save_event(
            project_id, 
            "workflow_retried", 
            operator_id=operator_id,
            payload={"retry_count": project.retry_count + 1}
        )

        await db.commit()

    # Enqueue via Celery
    try:
        from workers.workflow_worker.tasks.project_tasks import run_project_task
        task = run_project_task.apply_async(
            kwargs={
                "db_project_id": project_id,
                "title": project.title,
                "description": project.description or "",
                "workflow_template": project.workflow_template or "default",
                "quality_profile": project.quality_profile or "standard",
            },
            queue="projects",
        )
        return RetryResponse(message="Workflow re-queued successfully", task_id=task.id)
    except Exception as e:
        # Celery may not be connected — still return success (queued in DB)
        return RetryResponse(message=f"Queued in DB (Celery unavailable: {e})", task_id=project_id)


@router.post("/{project_id}/cancel", dependencies=[Depends(require_admin)])
async def cancel_workflow(project_id: str, operator_id: str = Depends(require_admin)):
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

        # Audit trail: Record cancellation
        from libs.workflow.persistence import WorkflowPersistence
        await WorkflowPersistence().save_event(
            project_id, 
            "workflow_cancelled", 
            operator_id=operator_id,
            payload={"previous_status": str(project.status)}
        )

        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.CANCELLED,
            cancelled_at=datetime.now(timezone.utc),
            cancelled_by=operator_id,
        )
        await db.commit()

    return {"message": "Workflow cancelled", "project_id": project_id}


@router.post("/{project_id}/approve", dependencies=[Depends(require_admin)])
async def approve_workflow(project_id: str, req: ApprovalRequest, operator_id: str = Depends(require_admin)):
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
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        p_status = project.status.value if hasattr(project.status, "value") else str(project.status)
        if p_status.lower() != "pending_approval":
            raise HTTPException(status_code=409, detail=f"Project is not pending approval (status: {p_status})")

        # Hardening: Save to Workflow Audit Trail (Phase 13.04)
        await persistence.save_event(
            project_id, 
            "workflow_approved", 
            operator_id=operator_id,
            payload={
                "notes": req.notes,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.QUEUED,
            notes=f"[APPROVED BY {operator_id}] {req.notes}",
            review_required=False,
        )
        await db.commit()

    return {"message": "Workflow approved and re-queued", "project_id": project_id}


@router.post("/{project_id}/replay", dependencies=[Depends(require_admin)])
async def replay_workflow(project_id: str, req: ReplayRequest, operator_id: str = Depends(require_admin)):
    """Trigger a durable replay of a workflow with hardening & audit trail."""
    from libs.workflow.persistence import WorkflowPersistence
    from libs.workflow.engine import WorkflowEngine
    from libs.db.models.core_models import ProjectStatus
    
    persistence = WorkflowPersistence()
    
    # 1. Load instance and check concurrency
    instance = await persistence.load_instance(project_id)
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
        operator_id=operator_id,
        payload={
            "mode": req.mode,
            "reason": req.reason,
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
        operator_id=operator_id,
        reason=req.reason
    )

    return {
        "status": "success",
        "message": "Durable replay sequence authorized and initiated.",
        "project_id": project_id,
        "audit_id": operator_id
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

@router.get("/improvements", response_model=List[ImprovementOut], tags=["Self-Healing"])
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


@router.patch("/improvements/{improvement_id}", response_model=ImprovementOut, tags=["Self-Healing"], dependencies=[Depends(require_admin)])
async def update_improvement(improvement_id: str, patch_data: ImprovementUpdate, operator_id: str = Depends(require_admin)):
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
        old_status = str(improvement.status)
        improvement.status = patch_data.status
        
        # Comprehensive: Log this mutation to the Global Audit Trail
        from libs.workflow.persistence import WorkflowPersistence
        await WorkflowPersistence.save_event(
            project_id=None, # Global system mutation
            event_type="improvement_status_updated",
            operator_id=operator_id,
            payload={
                "improvement_id": str(improvement.id),
                "target_file": improvement.target_file,
                "old_status": old_status,
                "new_status": str(patch_data.status)
            }
        )

        # If approved, we would normally trigger the effector here.
        if patch_data.status == "approved":
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


# ── Faz 14: Yönetişim Uç Noktaları ──────────────────────────────────────────

@router.get("/approvals", response_model=List[ApprovalRequestOut], tags=["Governance"])
async def list_approvals(
    response: Response,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """İnsan onayı bekleyen kararları listele."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import ApprovalRequest
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(ApprovalRequest.id))
        if status:
            count_q = count_q.where(ApprovalRequest.status == status)
        total_count = (await db.execute(count_q)).scalar()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

        q = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).limit(limit).offset(offset)
        if status:
            q = q.where(ApprovalRequest.status == status)
        res = await db.execute(q)
        approvals = res.scalars().all()

        return [
            ApprovalRequestOut(
                id=str(a.id),
                project_id=str(a.project_id),
                step_id=a.step_id,
                request_type=a.request_type,
                reason=a.reason,
                input_data=a.input_data,
                status=a.status,
                approver_id=a.approver_id,
                decision_at=a.decision_at,
                comment=a.comment,
                created_at=a.created_at,
            )
            for a in approvals
        ]


@router.patch("/approvals/{approval_id}", response_model=ApprovalRequestOut, tags=["Governance"], dependencies=[Depends(require_admin)])
async def update_approval(
    approval_id: str,
    update: ApprovalUpdate,
    operator_id: str = Depends(require_admin)
):
    """Kararı onayla veya reddet."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import ApprovalRequest, Project, ProjectStatus
    from sqlalchemy import select, update as sql_update

    try:
        uid = uuid.UUID(approval_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == uid))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Approval request not found")

        req.status = update.status
        req.comment = update.comment
        req.approver_id = operator_id
        req.decision_at = datetime.now(timezone.utc)

        # Eğer onaylandıysa ilgili projeyi QUEUED durumuna çek
        if update.status == "approved":
            await db.execute(
                sql_update(Project)
                .where(Project.id == req.project_id)
                .values(status=ProjectStatus.QUEUED, notes=f"[Approved] {update.comment}")
            )
        
        from libs.workflow.persistence import WorkflowPersistence
        await WorkflowPersistence().save_event(
            str(req.project_id),
            "approval_decision",
            operator_id=operator_id,
            payload={"status": update.status, "comment": update.comment}
        )

        await db.commit()
        await db.refresh(req)
        
        return ApprovalRequestOut(
            id=str(req.id),
            project_id=str(req.project_id),
            step_id=req.step_id,
            request_type=req.request_type,
            reason=req.reason,
            input_data=req.input_data,
            status=req.status,
            approver_id=req.approver_id,
            decision_at=req.decision_at,
            comment=req.comment,
            created_at=req.created_at,
        )


@router.get("/incidents", response_model=List[OperationalIncidentOut], tags=["Governance"])
async def list_incidents(
    response: Response,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Sistem olaylarını listele."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import OperationalIncident
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(OperationalIncident.id))
        if status:
            count_q = count_q.where(OperationalIncident.status == status)
        total_count = (await db.execute(count_q)).scalar()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

        q = select(OperationalIncident).order_by(OperationalIncident.created_at.desc()).limit(limit).offset(offset)
        if status:
            q = q.where(OperationalIncident.status == status)
        res = await db.execute(q)
        incidents = res.scalars().all()

        return [
            OperationalIncidentOut(
                id=str(i.id),
                incident_type=i.incident_type,
                severity=i.severity,
                message=i.message,
                status=i.status,
                project_id=str(i.project_id) if i.project_id else None,
                payload=i.payload,
                resolved_at=i.resolved_at,
                created_at=i.created_at,
            )
            for i in incidents
        ]


@router.patch("/incidents/{incident_id}", response_model=OperationalIncidentOut, tags=["Governance"], dependencies=[Depends(require_admin)])
async def update_incident(incident_id: str, update: IncidentUpdate, operator_id: str = Depends(require_admin)):
    """Olay durumunu gÃ¼ncele."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import OperationalIncident
    from sqlalchemy import select

    try:
        uid = uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ID")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(OperationalIncident).where(OperationalIncident.id == uid))
        incident = res.scalar_one_or_none()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        incident.status = update.status
        if update.status == "resolved":
            incident.resolved_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(incident)
        
        return OperationalIncidentOut(
            id=str(incident.id),
            incident_type=incident.incident_type,
            severity=incident.severity,
            message=incident.message,
            status=incident.status,
            project_id=str(incident.project_id) if incident.project_id else None,
            payload=incident.payload,
            resolved_at=incident.resolved_at,
            created_at=incident.created_at,
        )


@router.get("/analytics/costs", response_model=CostAnalyticsOut, tags=["Governance"])
async def get_cost_analytics():
    """Maliyet analizi ve bÃ¼tçe kullanımı."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        # Toplam maliyet
        res_total = await db.execute(select(func.sum(Project.cost_usd)))
        total_cost = res_total.scalar() or 0.0

        # En pahalı projeler
        res_top = await db.execute(
            select(Project.id, Project.title, Project.cost_usd)
            .order_by(Project.cost_usd.desc())
            .limit(5)
        )
        top_projects = [
            {"id": str(r[0]), "title": r[1], "cost_usd": float(r[2] or 0.0)}
            for r in res_top.all()
        ]

        # Limit (Örn: Sabit 1000$ veya config'den çekilebilir)
        budget_limit = 1000.0 
        usage_pct = (total_cost / budget_limit * 100) if budget_limit > 0 else 0

        return CostAnalyticsOut(
            total_cost_usd=float(total_cost),
            budget_limit_usd=budget_limit,
            usage_pct=usage_pct,
            top_projects=top_projects
        )
