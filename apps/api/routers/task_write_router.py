"""Görev Yazma Router — POST create, PATCH update, DELETE

Not: Cancel işlemi task_control_router.py içinde tanımlıdır (tek kaynak).
"""
from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone
from typing import Optional

from apps.api.routers.auth.jwt_auth import get_current_user, get_optional_user
from ._task_shared import _db_session, _project_to_dict, TaskCreateRequest, TaskUpdateRequest
from packages.observability.logging import get_logger

# V2 Mimarisi İçe Aktarımları
from schemas import TaskState
from packages.persistence.models import ProjectStatus, Project
from packages.persistence.session import AsyncSessionLocal
from packages.persistence.repositories.repository import ProjectRepository, TaskLogRepository
from packages.orchestration.application.task_routing import task_router
from packages.orchestration.application.job_queue import job_queue
from skills.base import SkillRequest
from skills.router import skill_router
from packages.orchestration.domain.events import event_bus
from config import DEERFLOW_ROLES

logger = get_logger("api.tasks.write")
router = APIRouter(prefix="/tasks", tags=["Görevler - Yazma"])

# ════════════════════════════════════════════════════════
# POST CREATE (DURUM MAKİNESİ VE CELERY ENTEGRELİ)
# ════════════════════════════════════════════════════════
@router.post("", summary="Yeni görev oluştur", status_code=201)
async def create_task(req: TaskCreateRequest, current_user=Depends(get_current_user)):
    # 0. Circuit Breaker (Faz 12 Hardening)
    try:
        from packages.healing.application.heal_engine import heal_engine
        health_score = heal_engine.system_health_score()
        if health_score < 0.35:
            logger.warning(f"Circuit Breaker tetiklendi! Skor: {health_score}")
            raise HTTPException(
                status_code=503, 
                detail=f"Sistem koruma modunda (Sağlık Skoru: {health_score:.2f}). Lütfen biraz bekleyin."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Circuit Breaker kontrol hatası (atlandı): {e}")

    db_project_id = ""

    # Açıklamaya context ekle
    full_description = req.description
    if req.context:
        full_description += f"\n\n--- Ek Bağlam ---\n{req.context}"

    try:
        async with AsyncSessionLocal() as db:
            # 1. State: CREATED (Görev API'den alındı ve DB'ye yazılıyor)
            p = await ProjectRepository.create(
                db=db,
                title=req.title,
                description=full_description,
                job_id="pending_celery_id",
                source=req.source,
                priority=req.priority,
                tags=req.tags,
                deadline=req.deadline,
                assigned_agent=req.assigned_agent,
                notes=req.notes,
                budget_limit=getattr(req, "budget_limit", 0.0),
                status=ProjectStatus.PENDING.value,
                workflow_template=req.workflow_template,
                quality_profile=req.quality_profile,
                acceptance_criteria=req.acceptance_criteria
            )
            
            pid = p.id
            db_project_id = str(pid)
            
            await TaskLogRepository.write(
                db, pid, TaskState.PENDING.value,
                f"Dashboard üzerinden oluşturuldu | Öncelik: {req.priority}",
                agent_id=str(current_user.id) if current_user else "dashboard",
                payload={"source": req.source, "priority": req.priority},
            )
            await db.commit()
            project_dict = _project_to_dict(p)
            
    except Exception as e:
        logger.error(f"Görev DB kaydı başarısız: {e}")
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

    # 2. Kuyruğa Gönder (QUEUED Fazı) — Canonical JobQueue Standardı
    try:
        user_id_str = str(current_user.id) if current_user else "system"
        
        # job_queue hem Celery'yi hem de in-memory'yi şeffaf yönetir
        task_name = "run_project"
        tags = req.tags or []

        # ── Semantic Task Routing (Automatic Agent Selection) ─────
        from config import DEERFLOW_ROLES  # type: ignore
        
        # Determine the target task_name (role)
        if req.assigned_agent in DEERFLOW_ROLES:
            # Explicit role mapping: deerflow_planner → deerflow_plan, etc.
            role_map = {
                "deerflow_planner": "deerflow_plan",
                "deerflow_researcher": "deerflow_research",
                "deerflow_reviewer": "deerflow_review",
                "deerflow_recovery": "deerflow_recovery",
            }
            task_name = role_map.get(req.assigned_agent, "deerflow_run")
            logger.info(f"Explicit routing task {db_project_id} to DeerFlow role: {task_name}")
            
        elif req.assigned_agent == "deerflow" or "deerflow" in tags or req.source == "research":
            # Context-based auto-routing (tags/source)
            priority = getattr(req, "priority", "medium")
            if priority == "critical" or any(t in tags for t in ["architecture", "refactor", "migration"]):
                task_name = "deerflow_plan"
            elif req.source == "research" or any(t in tags for t in ["research", "analysis", "investigate"]):
                task_name = "deerflow_research"
            elif any(t in tags for t in ["review", "audit", "quality"]):
                task_name = "deerflow_review"
            elif any(t in tags for t in ["fix", "recovery", "hotfix", "incident"]):
                task_name = "deerflow_recovery"
            else:
                task_name = "deerflow_run"
            logger.info(f"Context auto-routing task {db_project_id} to DeerFlow: {task_name}")

        elif not req.assigned_agent or req.assigned_agent == "auto":
            # Semantic routing based on title and description (as fallback)
            logger.info(f"Starting semantic routing for task: {req.title}")
            task_name = await task_router.route_task(req.title, full_description)
            logger.info(f"Semantic routing result for {db_project_id}: {task_name}")
        
        else:
            # Standard single agent or DAG
            task_name = "run_project"



        # ── Skill Suggestion (Phase 12.2 Integration) ─────
        skill_req = SkillRequest(
            task_type="project_create",
            title=req.title,
            description=full_description,
            project_id=db_project_id,
            agent_id=req.assigned_agent or None,
            context={
                "priority": getattr(req, "priority", "medium"),
                "tags": tags,
                "source": req.source,
                "routing_task_name": task_name,
            },
        )
        suggested_skills = skill_router.suggest(skill_req)
        logger.info(f"Task {db_project_id} için önerilen skill'ler: {suggested_skills}")
        
        # ── Suggested Skill'leri Context'e Yaz (Faz 12.2) ──
        if suggested_skills:
            try:
                async with AsyncSessionLocal() as db:
                    # p.execution_context bir JSONB, dict olarak alıp güncelleyelim
                    p_to_update = await ProjectRepository.get(db, pid)
                    if p_to_update:
                        ctx = dict(p_to_update.execution_context or {})
                        ctx["suggested_skills"] = suggested_skills
                        await ProjectRepository.update_fields(db, pid, execution_context=ctx)
                        await db.commit()
                        logger.debug(f"Task {db_project_id} context güncellendi (suggested_skills).")
            except Exception as ctx_err:
                logger.warning(f"Skill context yazımı başarısız (atlandı): {ctx_err}")

        job = await job_queue.enqueue(
            task_name,
            db_project_id=db_project_id,
            title=req.title,
            description=full_description,
            user_id=user_id_str,
            suggested_skills=suggested_skills,
            workflow_template=req.workflow_template,
            quality_profile=req.quality_profile,
            acceptance_criteria=req.acceptance_criteria
        )
        
        async with AsyncSessionLocal() as db:
            pid = uuid.UUID(db_project_id)
            await ProjectRepository.set_job_id(db, pid, job.id)
            await ProjectRepository.update_fields(db, pid, status=TaskState.QUEUED.value)
            await TaskLogRepository.write(
                db, pid, TaskState.QUEUED.value,
                f"Görev kuyruğa aktarıldı | İş ID: {job.id}",
                agent_id="orchestrator",
                payload={
                    "job_id": job.id,
                    "routing_task_name": task_name,
                    "suggested_skills": suggested_skills,
                },
            )
            await db.commit()
        project_dict["job_id"] = job.id
        project_dict["status"] = TaskState.QUEUED.value

    except Exception as e:
        logger.error(f"Celery/Job Queue hatası: {e}")
        # 3. State: ERROR (Kuyruğa gönderilemedi)
        async with AsyncSessionLocal() as db:
            if db_project_id:
                pid = uuid.UUID(db_project_id)
                await ProjectRepository.update_fields(db, pid, status=ProjectStatus.ERROR.value)
                await TaskLogRepository.write(
                    db, pid, ProjectStatus.ERROR.value,
                    f"Kuyruk Hatası: {str(e)}",
                    agent_id="system",
                    payload={"error": str(e), "failed_at": "enqueue"}
                )
                await db.commit()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Görev DB'ye kaydedildi (ID: {db_project_id}) ancak kuyruğa alınamadı: {str(e)}"
        )

    # Event yayını
    try:
        await event_bus.emit(
            "project.started",
            title=req.title, project_id=project_dict["job_id"],
            severity="info", agent_id="dashboard",
            phase="project",
            message=f"Dashboard'dan yeni görev: {req.title}",
        )
    except Exception:
        pass

    return project_dict


# ════════════════════════════════════════════════════════
# PATCH UPDATE
# ════════════════════════════════════════════════════════
@router.patch("/{task_id}", summary="Görev günceller")
async def update_task(task_id: str, req: TaskUpdateRequest, current_user=Depends(get_current_user)):
    try:
        update_data = {k: v for k, v in req.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=422, detail="Güncellenecek alan belirtilmedi")
            
        # V2 Güvenlik: Kullanıcı REST API'den görevin "status"unu manuel kafasına göre değiştiremez!
        if "status" in update_data:
            raise HTTPException(status_code=403, detail="Durum (status) alanı manuel güncellenemez. State Machine kullanın.")

        async with AsyncSessionLocal() as db:
            try:
                pid = uuid.UUID(task_id)
            except ValueError:
                p = await ProjectRepository.get_by_job_id(db, task_id)
                if not p:
                    raise HTTPException(status_code=404, detail="Görev bulunamadı")
                pid = p.id

            await ProjectRepository.update_fields(db, pid, **update_data)
            await TaskLogRepository.write(
                db, pid, "updated",
                f"Güncellenen alanlar: {list(update_data.keys())}",
                agent_id=str(current_user.id) if current_user else "dashboard",
                payload=update_data,
            )
            await db.commit()

        return {"updated": True, "fields": list(update_data.keys())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# DELETE
# ════════════════════════════════════════════════════════
@router.delete("/{task_id}", summary="Görev sil")
async def delete_task(task_id: str, current_user=Depends(get_current_user)):
    try:
        async with AsyncSessionLocal() as db:
            try:
                pid = uuid.UUID(task_id)
            except ValueError:
                p = await ProjectRepository.get_by_job_id(db, task_id)
                if not p:
                    raise HTTPException(status_code=404, detail="Görev bulunamadı")
                pid = p.id

            from sqlalchemy import delete as sql_delete
            await db.execute(sql_delete(Project).where(Project.id == pid))
            await db.commit()

        return {"deleted": True, "id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
