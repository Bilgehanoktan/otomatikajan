"""Görev Kontrol Router — cancel, retry, stop, copy"""
from fastapi import APIRouter, HTTPException, Body, Depends
from apps.api.routers.auth.jwt_auth import get_current_user
from ._task_shared import _db_session, _project_to_dict
from packages.observability.logging import get_logger
import uuid

logger = get_logger("api.tasks.control")
router = APIRouter(prefix="/tasks", tags=["Görevler - Kontrol"])

def _ensure_queue_capability(job_queue, capability: str, operation: str) -> None:
    """Aktif queue backend'in ilgili işlemi destekleyip desteklemediğini kontrol eder."""
    caps = getattr(job_queue, "capabilities", None)
    supported = getattr(caps, capability, None)
    # Dataclass yoksa eski flag'lere bak (fallback)
    if supported is None:
        supported = getattr(job_queue, capability, False)
    
    if not supported:
        raise HTTPException(
            status_code=409,
            detail=f"Aktif queue backend ({getattr(job_queue, 'backend_name', 'unknown')}) bu işlem için gerçek destek sunmuyor: {operation}",
        )


@router.get("/capabilities", summary="Queue backend yetenekleri")
async def queue_capabilities(current_user=Depends(get_current_user)):
    """Aktif queue backend'inin desteklediği operasyonları döner.

    Dashboard bu endpoint'i kullanarak pause/resume/cancel
    butonlarını dinamik olarak gösterir veya gizler.
    """
    from packages.orchestration.application.job_queue import job_queue
    caps = getattr(job_queue, "capabilities", None)
    if not caps:
        return {"backend_name": getattr(job_queue, "backend_name", "unknown")}
    return {
        "backend_name": caps.backend_name,
        "supports_cancel": caps.supports_cancel,
        "supports_pause": caps.supports_pause,
        "supports_resume": caps.supports_resume,
        "supports_listing": caps.supports_listing,
        "supports_registration": caps.supports_registration,
        "supports_dead_letters": caps.supports_dead_letters,
        "listing_scope": caps.listing_scope,
    }

@router.post("/{task_id}/cancel", summary="Görevi iptal et")
async def cancel_task(task_id: str, body: dict = Body(default={}), current_user=Depends(get_current_user)):
    cancelled_by = str(body.get("cancelled_by", "dashboard"))
    try:
        import uuid as _uuid
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository, TaskLogRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
                p   = await ProjectRepository.get(db, pid)
            except ValueError:
                p   = await ProjectRepository.get_by_job_id(db, task_id)
            if not p:
                raise HTTPException(status_code=404, detail="Görev bulunamadı")
            pid = p.id

            if p.status in ("COMPLETED", "CANCELLED", "completed", "cancelled"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Görev zaten {p.status} durumunda, iptal edilemez",
                )

            # In-process queue'da gerçek iptal sinyali gönder
            queue_job_id = p.job_id or task_id
            try:
                from packages.orchestration.application.job_queue import job_queue
                _ensure_queue_capability(job_queue, "supports_cancel", "cancel")
                job_queue.request_cancel(queue_job_id)
            except Exception as _qe:
                logger.warning(f"Queue cancel sinyali başarısız: {_qe}")

            await ProjectRepository.cancel(db, pid, cancelled_by=cancelled_by)
            await TaskLogRepository.write(
                db, pid, "cancelled",
                f"İptal edildi: {cancelled_by} (queue_job={queue_job_id})",
                level="warning", agent_id=cancelled_by,
            )
            await db.commit()

        from packages.orchestration.domain.events import event_bus
        await event_bus.emit(
            "project.failed",
            project_id=task_id,
            severity="warning",
            agent_id=cancelled_by,
            phase="project",
            message=f"Görev iptal edildi",
        )
        return {"cancelled": True, "id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# RETRY
# ════════════════════════════════════════════════════════
@router.post("/{task_id}/retry", summary="Başarısız görevi tekrar dene")
async def retry_task(task_id: str, current_user=Depends(get_current_user)):
    try:
        import uuid as _uuid
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository, TaskLogRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
                p   = await ProjectRepository.get(db, pid)
            except ValueError:
                p   = await ProjectRepository.get_by_job_id(db, task_id)

            if not p:
                raise HTTPException(status_code=404, detail="Görev bulunamadı")
            if p.status.upper() not in ("ERROR", "CANCELLED"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Sadece ERROR/CANCELLED görevler tekrar denenebilir (şu an: {p.status})"
                )

            await ProjectRepository.increment_retry(db, p.id)
            # State: FAILED/CANCELLED -> PENDING (retry başlamadan önce)
            await ProjectRepository.update_fields(db, p.id,
                status="PENDING", error_detail="",
            )
            await TaskLogRepository.write(
                db, p.id, "retry",
                f"Retry #{p.retry_count + 1} başlatıldı",
                level="info", agent_id="dashboard",
            )
            await db.commit()
            proj_title = p.title
            proj_desc  = p.description
            proj_uuid  = p.id

        # Yeni job kuyruğa al — job.id = yeni canonical queue id
        from packages.orchestration.application.job_queue import job_queue
        job = await job_queue.enqueue(
            "run_project",
            db_project_id=str(proj_uuid),
            job_id=str(uuid.uuid4())[:12],
            title=proj_title,
            description=proj_desc,
            user_id=str(current_user.id),
            workflow_template=getattr(p, "workflow_template", "default"),
            quality_profile=getattr(p, "quality_profile", "standard"),
            acceptance_criteria=getattr(p, "acceptance_criteria", []),
            execution_context=getattr(p, "execution_context", {})
        )
        # DB'deki job_id alanını yeni job ile senkronize et
        try:
            import uuid as _uuid2
            from packages.persistence.session import AsyncSessionLocal as _ASL
            from packages.persistence.repositories.repository import ProjectRepository as _PR2
            async with _ASL() as _db2:
                await _PR2.set_job_id(_db2, proj_uuid, job.id)
                await _db2.commit()
        except Exception as _je:
            logger.warning(f"Retry job_id sync başarısız: {_je}")

        return {"retrying": True, "id": task_id, "new_job_id": job.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# STOP (çalışan görevi durdur)
# ════════════════════════════════════════════════════════
@router.post("/{task_id}/stop", summary="Çalışan görevi durdur")
async def stop_task(task_id: str, current_user=Depends(get_current_user)):
    """
    Job queue'daki çalışan işi iptal eder.
    Not: Zaten başlamış LLM çağrıları kesilmez — DB kaydı güncellenir.
    """
    try:
        import uuid as _uuid
        from packages.orchestration.application.job_queue import job_queue
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository, TaskLogRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
                p   = await ProjectRepository.get(db, pid)
            except ValueError:
                p   = await ProjectRepository.get_by_job_id(db, task_id)
            if not p:
                raise HTTPException(status_code=404, detail="Görev bulunamadı")
            pid = p.id

            if p.status.upper() in ("COMPLETED", "CANCELLED"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Görev {p.status} durumunda, durdurulamaz",
                )

            # In-process queue'ya gerçek cancel sinyali gönder
            queue_job_id = p.job_id or str(p.id)
            _ensure_queue_capability(job_queue, "supports_cancel", "stop")
            cancelled_ok = job_queue.request_cancel(queue_job_id)
            
            if not cancelled_ok:
                logger.warning(f"[CANCEL] Kuyruk işlemi reddetti (zaten bitmiş olabilir): {queue_job_id}")
                # Kuyruk reddetmiş olsa bile (belki PENDING değildir), DB'de RUNNING ise 
                # ve biz durdurmak istiyorsak, DB üzerinden zorlayabiliriz.
                # Ancak 'honesty' prensibi gereği, kuyruk durduramadıysa kullanıcıya bildiriyoruz.
                raise HTTPException(
                    status_code=409, 
                    detail="Görev kuyruk seviyesinde durdurulamadı. Görev zaten tamamlanmış veya sistem meşgul olabilir."
                )

            # DB durumunu güncelle (Atomic Status Guard ile)
            updated = await ProjectRepository.cancel(db, pid, cancelled_by=f"user:{current_user.id}")
            
            if updated:
                await TaskLogRepository.write(
                    db, pid, "stopped",
                    f"Durduruldu (queue_job={queue_job_id})",
                    level="warning", agent_id="dashboard",
                )
                await db.commit()
                logger.info(f"[STOP] Task {pid} marked as CANCELLED in DB.")
            else:
                logger.warning(f"[STOP] Task {pid} DB sync skipped (already finished/error).")
                # Eğer DB güncellenemediyse, büyük ihtimalle o arada bitti.
                # Bu durumda 409 dönmek daha dürüst olur.
                raise HTTPException(
                    status_code=409, 
                    detail="Görev DB seviyesinde durdurulamadı. Muhtemelen o anda tamamlandı."
                )
 
        return {"stopped": True, "id": task_id, "signal_sent": cancelled_ok}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# PAUSE / RESUME
# ════════════════════════════════════════════════════════
@router.post("/{task_id}/pause", summary="Görevi duraklat")
async def pause_task(task_id: str, current_user=Depends(get_current_user)):
    try:
        import uuid as _uuid
        from packages.orchestration.application.job_queue import job_queue
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository, TaskLogRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
                p   = await ProjectRepository.get(db, pid)
            except ValueError:
                p   = await ProjectRepository.get_by_job_id(db, task_id)
            if not p:
                raise HTTPException(status_code=404, detail="Görev bulunamadı")
            pid = p.id

            # status control atlanmamalı
            # if p.status != "running": ...  ancak pause logic'te running olması yeterli
            
            queue_job_id = p.job_id or task_id
            _ensure_queue_capability(job_queue, "supports_pause", "pause")
            paused_ok = job_queue.pause_job(queue_job_id)

            if paused_ok:
                await ProjectRepository.update_fields(db, pid, status="PAUSED")
                await TaskLogRepository.write(
                    db, pid, "paused",
                    f"Duraklatıldı (queue_job={queue_job_id})",
                    level="info", agent_id="dashboard",
                )
                await db.commit()
                logger.info(f"[PAUSE] Task {pid} successfully paused.")
            else:
                logger.warning(f"[PAUSE] Kuyruk işlemi reddetti (zaten PAUSED veya bitmiş olabilir): {queue_job_id}")
                raise HTTPException(
                    status_code=409, 
                    detail="Görev kuyruk seviyesinde duraklatılamadı. Görev zaten duraklatılmış, tamamlanmış veya sistem meşgul olabilir."
                )

        return {"paused": True, "id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/resume", summary="Durdurulmuş görevi devam ettir")
async def resume_task(task_id: str, current_user=Depends(get_current_user)):
    try:
        import uuid as _uuid
        from packages.orchestration.application.job_queue import job_queue
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository, TaskLogRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
                p   = await ProjectRepository.get(db, pid)
            except ValueError:
                p   = await ProjectRepository.get_by_job_id(db, task_id)
            if not p:
                raise HTTPException(status_code=404, detail="Görev bulunamadı")
            pid = p.id

            queue_job_id = p.job_id or task_id
            _ensure_queue_capability(job_queue, "supports_resume", "resume")
            resumed_ok = job_queue.resume_job(queue_job_id)

            if resumed_ok:
                await ProjectRepository.update_fields(db, pid, status="RUNNING")
                await TaskLogRepository.write(
                    db, pid, "resumed",
                    f"Devam ettirildi (queue_job={queue_job_id})",
                    level="info", agent_id="dashboard",
                )
                await db.commit()
                logger.info(f"[RESUME] Task {pid} successfully resumed.")
            else:
                logger.warning(f"[RESUME] Kuyruk işlemi reddetti: {queue_job_id}")
                raise HTTPException(
                    status_code=409, 
                    detail="Görev kuyruk seviyesinde devam ettirilemedi. Görev zaten çalışıyor, tamamlanmış veya sistem meşgul olabilir."
                )

        return {"resumed": True, "id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# COPY
# ════════════════════════════════════════════════════════
@router.post("/{task_id}/copy", summary="Görevi kopyala")
async def copy_task(task_id: str, body: dict = Body(default={}), current_user=Depends(get_current_user)):
    new_title    = body.get("title", "")
    new_priority = body.get("priority", "")
    try:
        import uuid as _uuid
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository, TaskLogRepository

        async with AsyncSessionLocal() as db:
            try:
                pid = _uuid.UUID(task_id)
                src = await ProjectRepository.get(db, pid)
            except ValueError:
                src = await ProjectRepository.get_by_job_id(db, task_id)

            if not src:
                raise HTTPException(status_code=404, detail="Görev bulunamadı")

            new_job_id = str(uuid.uuid4())[:12]
            title      = new_title or f"[Kopya] {src.title}"
            priority   = new_priority or src.priority

            new_p = await ProjectRepository.create(
                db,
                title=title,
                description=src.description,
                job_id=new_job_id,
                source="manual",
                priority=priority,
                tags=src.tags or [],
                assigned_agent=src.assigned_agent or "",
                notes=src.notes or "",
                workflow_template=getattr(src, "workflow_template", "default"),
                quality_profile=getattr(src, "quality_profile", "standard"),
                acceptance_criteria=getattr(src, "acceptance_criteria", []),
                execution_context=getattr(src, "execution_context", {})
            )
            await TaskLogRepository.write(
                db, new_p.id, "created",
                f"{task_id} görevinden kopyalandı",
                agent_id="dashboard",
            )
            await db.commit()
            copied_id  = str(new_p.id)

        # Job queue'ya ekle
        from packages.orchestration.application.job_queue import job_queue
        job = await job_queue.enqueue(
            "run_project",
            db_project_id=copied_id,
            job_id=new_job_id,
            title=title,
            description=src.description,
            user_id=str(current_user.id),
            workflow_template=getattr(src, "workflow_template", "default"),
            quality_profile=getattr(src, "quality_profile", "standard"),
            acceptance_criteria=getattr(src, "acceptance_criteria", []),
            execution_context=getattr(src, "execution_context", {})
        )

        # job_id'yi DB'ye geri yaz (queue job.id = canonical id — create/retry ile tutarlı)
        try:
            import uuid as _uuid2
            from packages.persistence.session import AsyncSessionLocal as _ASL
            from packages.persistence.repositories.repository import ProjectRepository as _PR
            async with _ASL() as _db2:
                await _PR.set_job_id(_db2, _uuid2.UUID(copied_id), job.id)
                await _db2.commit()
        except Exception as _je:
            logger.warning(f"copy_task job_id sync başarısız: {_je}")

        return {"copied": True, "new_id": copied_id, "new_job_id": job.id, "title": title}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# LOGS
# ════════════════════════════════════════════════════════
