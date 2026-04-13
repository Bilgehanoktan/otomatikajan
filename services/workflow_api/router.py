"""
Workflow Control Plane API — Phase 13.04
Exposes workflow runs, step details, retry/replay, and approval controls.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[ProjectListItem])
async def list_workflows(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all projects/workflows with step summary."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, SubTask, ProjectStatus
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
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
    """Get full workflow detail with step trace."""
    project, subtasks = await _get_project_with_subtasks(project_id)
    return _map_workflow(project, subtasks)


@router.post("/{project_id}/retry", response_model=RetryResponse)
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
async def approve_workflow(project_id: str, notes: str = ""):
    """Approve a workflow pending manual review."""
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
        if p_status.lower() != "pending_approval":
            raise HTTPException(status_code=409, detail=f"Project is not pending approval (status: {p_status})")

        await ProjectRepository.update_fields(
            db, project.id,
            status=ProjectStatus.QUEUED,
            notes=f"[APPROVED] {notes}",
            review_required=False,
        )
        await db.commit()

    return {"message": "Workflow approved and re-queued", "project_id": project_id}


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
