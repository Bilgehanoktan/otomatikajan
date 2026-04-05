"""Görev Okuma Router — GET endpoints"""
from fastapi import APIRouter, HTTPException, Query, Depends
from apps.api.routers.auth.jwt_auth import get_current_user
from ._task_shared import _db_session, _project_to_dict
from packages.observability.logging import get_logger

from typing import Optional, List, Dict, Any

logger = get_logger("api.tasks.read")
router = APIRouter(prefix="/tasks", tags=["Görevler - Okuma"])

@router.get("", summary="Görev listesi")
async def list_tasks(
    status:   str | None = Query(None, enum=["PENDING", "QUEUED", "RUNNING", "PENDING_APPROVAL", "COMPLETED", "PARTIAL_COMPLETE", "ERROR", "CANCELLED", "PAUSED", "RETRYING"]),
    source:   Optional[str] = Query(None, description="manual|api|telegram|scheduled"),
    priority: Optional[str] = Query(None),
    search:   Optional[str] = Query(None, description="Başlıkta arama"),
    limit:    int = Query(50, ge=1, le=200),
    offset:   int = Query(0, ge=0),
    current_user=Depends(get_current_user),
):
    try:
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import ProjectRepository
        from sqlalchemy import select, func
        from packages.persistence.models import Project
        async with AsyncSessionLocal() as db:
            # ── Faz 12.1A: Compatibility Shim ───────────────
            status_map = {
                "done": "COMPLETED",
                "failed": "ERROR",
                "success": "COMPLETED",
                "waiting": "PENDING",
                "active": "RUNNING",
                "todo": "PENDING"
            }
            status_val = status.lower() if status else None
            db_status = status_map.get(status_val, status_val.upper() if status_val else None)

            projects = await ProjectRepository.list_recent(
                db, limit=limit, offset=offset, status=db_status,
                source=source, priority=priority, search=search,
            )
            # Total count for pagination
            count_q = select(func.count(Project.id))
            if db_status:
                count_q = count_q.where(Project.status == db_status)
            if source:
                count_q = count_q.where(Project.source == source)
            if priority:
                count_q = count_q.where(Project.priority == priority)
            if search:
                count_q = count_q.where(Project.title.ilike(f"%{search}%"))
            total_result = await db.execute(count_q)
            total = total_result.scalar() or 0

        return {
            "total":    total,
            "limit":    limit,
            "offset":   offset,
            "tasks":    [_project_to_dict(p) for p in projects],
            "is_fallback": False,
            "source_of_truth": "database"
        }
    except Exception as e:
        logger.warning(f"DB görev listesi başarısız, fallback: {e}")
        # in-memory fallback
        try:
            from packages.orchestration.context import orchestrator
            tasks = orchestrator.list_tasks()
            return {
                "total":  len(tasks),
                "tasks":  [
                    {"id": t.id, "title": t.title, "status": str(t.status),
                     "source": "api", "priority": "medium", "progress_pct": 0}
                    for t in tasks[-limit:]
                ],
                "is_fallback": True,
                "source_of_truth": "orchestrator_memory",
                "degraded_reason": str(e)
            }
        except Exception:
            return {"total": 0, "tasks": [], "is_fallback": True, "source_of_truth": "empty_fallback"}


@router.get("/capabilities", summary="Sistemin otonom yetenek ve uzman ajan listesi")
async def task_capabilities(current_user=Depends(get_current_user)):
    """Sistemin otonom olarak hangi uzmanlıklara sahip olduğunu döner."""
    try:
        from packages.orchestration.agency.loader import agency_loader
        agents = agency_loader.list_agents()
        return {
            "capabilities": [
                {
                    "id": a["id"], 
                    "name": a.get("id", "Unknown").capitalize(),
                    "description": a.get("description", ""),
                    "category": a.get("category", "general")
                } 
                for a in agents
            ],
            "total_specialists": len(agents),
            "source_of_truth": "agency_loader"
        }
    except Exception as e:
        logger.error(f"Failed to load capabilities: {e}")
        return {"capabilities": [], "total_specialists": 0, "error": str(e)}


# ════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════
@router.get("/stats/summary", summary="Görev istatistik özeti")
async def tasks_summary(current_user=Depends(get_current_user)):
    try:
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import ProjectRepository
        async with AsyncSessionLocal() as db:
            counts = await ProjectRepository.counts_by_status(db)
            total_cost = await ProjectRepository.get_total_cost(db) # Get cost while session is open

        total = sum(counts.values())
        completed = counts.get("completed", 0)
        errored   = counts.get("error", 0)
        
        return {
            "total":     total,
            "pending":   counts.get("pending", 0),
            "queued":    counts.get("queued", 0),
            "running":   counts.get("running", 0),
            "pending_approval": counts.get("pending_approval", 0),
            "completed": completed,
            "partial_complete": counts.get("partial_complete", 0),
            "error":     errored,
            "cancelled": counts.get("cancelled", 0),
            "paused":    counts.get("paused", 0),
            "success_rate": round(
                (completed + counts.get("partial_complete", 0)) / (total or 1) * 100, 1
            ) if total else 0.0,
            
            "cost":      total_cost,

            # Kaynak-bazlı backward compatibility
            "failed":    errored,
            "is_fallback": False,
            "source_of_truth": "database"
        }
    except Exception:
        try:
            from packages.orchestration.context import orchestrator
            tasks = orchestrator.list_tasks()
            from collections import Counter
            c = Counter(str(t.status) for t in tasks)
            total = len(tasks)
            completed = c.get("completed", 0)
            errored   = c.get("error", 0)
            return {
                "total":     total,
                "pending":   c.get("pending", 0),
                "running":   c.get("running", 0),
                "completed": completed,
                "error":     errored,
                "cancelled": 0,
                "done":      completed,
                "failed":    errored,
                "is_fallback": True,
                "source_of_truth": "orchestrator_memory"
            }
        except Exception:
            return {"total": 0, "pending": 0, "running": 0, "completed": 0, "error": 0, "done": 0, "failed": 0, "is_fallback": True, "source_of_truth": "empty_fallback"}


@router.get("/{task_id}", summary="Görev detayı")
async def get_task(task_id: str, current_user=Depends(get_current_user)):
    try:
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import ProjectRepository, SubTaskRepository, TaskLogRepository
        from sqlalchemy import select
        from packages.persistence.models import Project
        import uuid as _uuid

        async with AsyncSessionLocal() as db:
            # UUID veya job_id ile ara
            p = None
            try:
                pid = _uuid.UUID(task_id)
                p   = await ProjectRepository.get(db, pid)
            except ValueError:
                pass

            if not p:
                p = await ProjectRepository.get_by_job_id(db, task_id)

            if not p:
                raise HTTPException(status_code=404, detail="Görev bulunamadı")

            subtasks = await SubTaskRepository.get_by_project(db, p.id)
            logs     = await TaskLogRepository.get_by_project(db, p.id, limit=100)

            # --- AGI Entegrasyonu (Gelişmiş Episode Verisi) ---
            from packages.persistence.models import Memory
            from sqlalchemy import select
            agi_metadata = None
            # Project ID ile eşleşen en son episode kaydını al
            agi_q = select(Memory).where(
                Memory.project_id == str(p.id),
                Memory.category == "episode_record"
            ).order_by(Memory.created_at.desc()).limit(1)
            
            agi_res = await db.execute(agi_q)
            agi_mem = agi_res.scalar_one_or_none()
            if agi_mem:
                agi_metadata = agi_mem.metadata_

        return _project_to_dict(p, subtasks=subtasks, logs=logs, agi_metadata=agi_metadata)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Görev detayı alınamadı: {e}")


# ════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════
@router.get("/{task_id}/logs", summary="Görev log geçmişi")
async def task_logs(task_id: str, limit: int = Query(100, ge=1, le=500), current_user=Depends(get_current_user)):
    try:
        import uuid as _uuid
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import ProjectRepository, TaskLogRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
            except ValueError:
                p   = await ProjectRepository.get_by_job_id(db, task_id)
                if not p:
                    raise HTTPException(status_code=404, detail="Görev bulunamadı")
                pid = p.id

            logs = await TaskLogRepository.get_by_project(db, pid, offset=0, limit=limit)

        return [
            {
                "id":       str(l.id),
                "level":    l.level,
                "event":    l.event,
                "message":  l.message,
                "agent_id": l.agent_id,
                "payload":  l.payload,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# SUBTASKS
# ════════════════════════════════════════════════════════
@router.get("/{task_id}/subtasks", summary="Alt görev listesi")
async def task_subtasks(task_id: str, current_user=Depends(get_current_user)):
    try:
        import uuid as _uuid
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import ProjectRepository, SubTaskRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
            except ValueError:
                p   = await ProjectRepository.get_by_job_id(db, task_id)
                if not p:
                    raise HTTPException(status_code=404, detail="Görev bulunamadı")
                pid = p.id

            subtasks = await SubTaskRepository.get_by_project(db, pid)

        return [
            {
                "id":           str(s.id),
                "agent_id":     s.agent_id,
                "status":       s.status,
                "attempts":     s.attempts,
                "is_complex":   s.is_complex,
                "parent_id":    str(s.parent_id) if s.parent_id else None,
                "recovered":    s.recovered,
                "llm_provider": s.llm_provider,
                "input_tokens": s.input_tokens,
                "output_tokens":s.output_tokens,
                "cost_usd":     s.cost_usd,
                "latency_s":    s.latency_s,
                "result_preview": (s.result[:500] + "…") if s.result and len(s.result) > 500 else (s.result or ""),
                "created_at":   s.created_at.isoformat() if s.created_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in subtasks
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# TRACEABILITY (Faz 13)
# ════════════════════════════════════════════════════════
@router.get("/{task_id}/skill-traces", summary="Beceri çalıştırılma izleri (Trace)")
async def task_skill_traces(
    task_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user)
):
    """Her beceri yürütme adımının detaylı kaydını döndürür."""
    try:
        import uuid as _uuid
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import ProjectRepository, SkillLogRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
            except ValueError:
                p = await ProjectRepository.get_by_job_id(db, task_id)
                if not p:
                    raise HTTPException(status_code=404, detail="Görev bulunamadı")
                pid = p.id

            logs = await SkillLogRepository.get_by_project(db, pid, limit=limit)

        return [
            {
                "id":         str(l.id),
                "skill_id":   l.skill_id,
                "agent_id":   l.agent_id,
                "success":    l.success,
                "summary":    l.summary,
                "data":       l.data,
                "duration_s": round(l.duration_s, 3),
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
