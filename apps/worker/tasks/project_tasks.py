import asyncio
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

import httpx
from celery import Task
from celery.utils.log import get_task_logger

from packages.persistence.models import ProjectStatus
from apps.worker.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


# ── Async Yardımcısı ──────────────────────────────────────
def run_async(coro):
    """Celery worker'ından async kod çalıştırır (Hardened for loop-reuse)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Eğer zaten bir loop varsa ve çalışıyorsa, bu senaryo Celery sync worker'da beklenmez.
        # Yine de destek için: nested loop gerekiyorsa nest_asyncio kullanılmalı.
        # Şimdilik en azından awaitable dönmemesi için hata fırlatabiliriz veya basitçe:
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(coro)

    # Yeni loop oluştur ve çalıştır
    new_loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(coro)
    finally:
        try:
            new_loop.close()
        except Exception:
            pass
        asyncio.set_event_loop(None)


# ── Proje Görevi (DÜZELTİLDİ: Contract uyumu + Repository Pattern) ──
@celery_app.task(
    name="tasks.project_tasks.run_project_task",
    bind=True,
    max_retries=3,
    acks_late=True,       # Worker çökerse görev Redis'te kalır, kaybolmaz!
    default_retry_delay=10,
    soft_time_limit=300,  # 5 dakika
    time_limit=360,
)
def run_project_task(
    self: Task, 
    db_project_id: str, 
    title: str, 
    description: str, 
    job_id: str = "", 
    user_id: str = "",
    workflow_template: str = "default",
    quality_profile: str = "standard",
    acceptance_criteria: list | None = None,
    execution_context: dict | None = None,
    db_subtask_map: dict | None = None
):
    """
    Projeyi arka planda çalıştır.
    Durum makinesini işletir (pending -> running -> done/failed).
    Orchestrator ProjectTask döner — FinalReport DEĞİL.
    """
    import uuid as _uuid
    logger.info(f"🚀 Worker görevi devraldı: {job_id or db_project_id} — {title}")

    async def _execute_task():
        from packages.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository
        from packages.orchestration.agi.task_governance import GovernanceStatus as AGIStatus

        async with AsyncSessionLocal() as db:
            # 1. State: Ajanlar çalışmaya başlıyor (pending -> running)
            p = await ProjectRepository.get(db, _uuid.UUID(db_project_id))
            if not p:
                logger.error(f"Proje bulunamadı: {db_project_id}")
                return {"status": "error", "reason": "not_found"}

            status_val = p.status.value if hasattr(p.status, "value") else str(p.status)
            if status_val in (ProjectStatus.RUNNING.value, ProjectStatus.COMPLETED.value, ProjectStatus.ERROR.value, ProjectStatus.CANCELLED.value):
                logger.warning(f"⏩ Proje {p.id} zaten '{status_val}' durumunda. Tekrar çalıştırılmayacak (Idempotency).")
                return {"status": "skipped", "reason": "already_processed"}

            await ProjectRepository.mark_started(db, p.id)
            await db.commit()

        # 2. Asıl işi Nexus Orchestrator'a devret
        # Bu aşamada Nexus, planlama ve yürütmeyi (coordinate_goal) yapar.
        result_task = await orchestrator.coordinate_goal(
            title=title, 
            description=description, 
            project_id=db_project_id,
            workflow_template=workflow_template,
            quality_profile=quality_profile,
            acceptance_criteria=acceptance_criteria,
            execution_context=execution_context
        )
        
        # Result task zaten ProjectTask tipinde, worker akışı için döndür
        return result_task

    try:
        # Asenkron akışı çalıştır
        result = run_async(_execute_task())

        if isinstance(result, dict):
            # Erken dönen (Idempotency vb.) durumları işle
            if result.get("status") == "skipped":
                return result
            if result.get("status") == "error":
                raise Exception(f"Task error: {result.get('reason')}")

        # ProjectTask uyumlu alanlar (NexusOrchestrator'dan dönen nesne):
        # Durumları güvenle al
        has_failures = any(
            s.status in (AGIStatus.ERROR, AGIStatus.FAILED, AGIStatus.SKIPPED)
            for s in result.subtasks
        )
        final_status = ProjectStatus.PARTIAL_COMPLETE if has_failures else ProjectStatus.COMPLETED

        # DB'yi güncelle
        async def _mark_done():
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repositories.repository import ProjectRepository
            async with AsyncSessionLocal() as db:
                p = await ProjectRepository.get(db, _uuid.UUID(db_project_id))
                if p:
                    await ProjectRepository.mark_completed(
                        db, p.id,
                        report=result.report or "",
                        status=final_status.value,
                    )
                    await db.commit()
        run_async(_mark_done())

        # Tamamlandı webhook'u
        send_webhook_task.apply_async(
            kwargs={
                "event": "project.completed",
                "payload": {
                    "project_id": job_id or db_project_id,
                    "status": final_status.value,
                    "user_id": user_id,
                },
            },
            queue="background",
        )
        terminal_id = job_id or db_project_id
        logger.info(f"✅ Proje tamamlandı: {terminal_id} | Durum: {final_status.value}")
        return {"status": "success", "task_id": terminal_id}

    except Exception as exc:
        logger.error(f"❌ Proje hatası ({job_id or db_project_id}): {exc}")

        async def _set_failed():
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repositories.repository import ProjectRepository
            async with AsyncSessionLocal() as db:
                p = await ProjectRepository.get(db, _uuid.UUID(db_project_id))
                if p:
                    await ProjectRepository.set_error(db, p.id, str(exc))
                    await db.commit()

        # State: Görev çöktü olarak işaretle
        run_async(_set_failed())

        # Webhook: Hata bildirimi
        send_webhook_task.apply_async(
            kwargs={
                "event": "project.failed",
                "payload": {"project_id": job_id or db_project_id, "error": str(exc), "user_id": user_id},
            },
            queue="background",
        )
        # Celery tekrar deneme (Retry) tetiklemesi
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 10)


# ── Webhook Gönderimi (Korundu) ───────────────────────────
@celery_app.task(
    name="tasks.project_tasks.send_webhook_task",
    bind=True,
    max_retries=5,
    default_retry_delay=30,
)
def send_webhook_task(self: Task, event: str, payload: dict):
    """
    Kayıtlı webhook abonelerine HMAC-SHA256 imzalı POST gönderir.
    """
    try:
        subscriptions = run_async(_get_subscriptions(event))
        if not subscriptions:
            return {"sent": 0}

        body = json.dumps({"event": event, "data": payload, "timestamp": datetime.now(timezone.utc).isoformat()})
        sent = 0

        for sub in subscriptions:
            sig = hmac.new(sub["secret"].encode(), body.encode(), hashlib.sha256).hexdigest()
            try:
                resp = httpx.post(
                    sub["url"],
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Event": event,
                        "X-Webhook-Signature": f"sha256={sig}",
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                sent += 1
                logger.info(f"📡 Webhook gönderildi -> {sub['url']} ({event})")
            except Exception as e:
                logger.warning(f"⚠️ Webhook başarısız -> {sub['url']}: {e}")

        return {"sent": sent, "total": len(subscriptions)}

    except Exception as exc:
        raise self.retry(exc=exc)


async def _get_subscriptions(event: str) -> list[dict]:
    from packages.persistence.session import AsyncSessionLocal
    from packages.persistence.models import WebhookSubscription
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        subs = (await db.execute(
            select(WebhookSubscription).where(WebhookSubscription.is_active == True)
        )).scalars().all()
        return [
            {"url": s.url, "secret": s.secret}
            for s in subs
            if event in s.events or "*" in s.events
        ]


# ── Periyodik Görevler (Korundu) ──────────────────────────
@celery_app.task(name="tasks.project_tasks.heal_check_task")
def heal_check_task():
    """Her 1 dakikada bir sağlık kontrolü."""
    try:
        from packages.healing.application.heal_engine import heal_engine
        score = heal_engine.system_health_score()
        logger.info(f"🩺 Sistem sağlık skoru: {score}")
        return {"health": score}
    except Exception as e:
        logger.error(f"Heal check hatası: {e}")


@celery_app.task(name="tasks.project_tasks.cleanup_memories")
def cleanup_memories():
    """Süresi dolmuş bellekleri temizle."""
    async def _clean():
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.models import Memory
        from sqlalchemy import delete

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(Memory).where(
                    Memory.expires_at != None,
                    Memory.expires_at < datetime.now(timezone.utc),
                )
            )
            await db.commit()
            return result.rowcount

    deleted = run_async(_clean())
    logger.info(f"🧹 {deleted} süresi dolmuş bellek silindi.")
    return {"deleted": deleted}


@celery_app.task(name="tasks.project_tasks.run_self_update_task")
def run_self_update_task(target_file_path: str, instruction: str):
    """Sistemin kendi kodunu asenkron olarak değiştirmesi."""
    async def _execute():
        from packages.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
        if not orchestrator.self_updater:
            return "Self-Updater aktif değil."
        return await orchestrator.self_updater.modify_system_file(
            target_file_path=target_file_path,
            instruction=instruction
        )
    return run_async(_execute())


@celery_app.task(name="tasks.project_tasks.run_visual_audit_task")
def run_visual_audit_task():
    """Arayüzü periyodik olarak denetler ve iyileştirme önerileri sunar."""
    async def _execute():
        from packages.observability.visual_util import capture_screenshot
        from packages.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ImprovementRepository
        
        try:
            # 1. Ekran görüntüsü al
            b64_img = await capture_screenshot()
            
            # 2. Vision ile analiz et
            prompt = """Antigravity AI Dashboard arayüzünü UX, UI ve görsel tutarlılık açısından analiz et. 
Sistem 'Mission Control' (karanlık mod, neon vurgular, glassmorphism) temasını kullanıyor.
Şunları kontrol et:
- Görsel hatalar (taşan metinler, hizalama vb.)
- UX eksiklikleri
- Erişilebilirlik sorunları

Bulgularını 'İyileştirme Fırsatı' formunda raporla."""
            
            analysis_text = await orchestrator.model_orch.complete_vision(prompt, b64_img, preferred_provider="gemini")
            
            # 3. Sonucu İyileştirme tablosuna kaydet
            async with AsyncSessionLocal() as db:
                await ImprovementRepository.create(
                    db,
                    title="Otomatik Görsel Denetim Raporu",
                    description=analysis_text,
                    source_type="visual_audit",
                    severity="medium",
                    category="ux_ui",
                    evidence="playwright_screenshot_b64"
                )
                await db.commit()
            
            logger.info("✅ Görsel denetim tamamlandı ve raporlandı.")
            return "Visual audit completed."
        except Exception as e:
            logger.error(f"❌ Görsel denetim hatası: {e}")
            return f"Error: {e}"

    return run_async(_execute())


@celery_app.task(name="tasks.project_tasks.run_market_intelligence_task")
def run_market_intelligence_task():
    """Pazar trendlerini analiz eder ve stratejik raporlar hazırlar."""
    async def _execute():
        from packages.integrations.web_search import get_web_search
        from packages.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ImprovementRepository
        import json
        
        try:
            # 1. Web Araması Yap
            search_tool = get_web_search()
            trends = await search_tool.search("AI coding agents trends 2026 site:techcrunch.com OR site:theverge.com")
            
            context = json.dumps(trends, ensure_ascii=False)
            prompt = f"Aşağıdaki güncel haberleri analiz et ve sistemin uzman ajanları için stratejik bir 'teknoloji radarı' oluştur:\n\n{context}"
            
            # 2. Strategist ile analiz et
            analysis = await orchestrator.model_orch.complete_task(
                agent_role="strategist",
                prompt=prompt,
                system_prompt="Sen teknoloji radarı ve stratejik planlama uzmanısın."
            )
            
            # 3. Sonucu İyileştirme tablosuna kaydet
            async with AsyncSessionLocal() as db:
                await ImprovementRepository.create(
                    db,
                    title="Haftalık Stratejik Trend Analizi",
                    description=analysis.content,
                    source_type="market_intel",
                    severity="low",
                    category="strategy"
                )
                await db.commit()
            
            logger.info("✅ Pazar zekası analizi tamamlandı.")
            return "Market intelligence completed."
        except Exception as e:
            logger.error(f"❌ Pazar zekası hatası: {e}")
            return f"Error: {e}"

    return run_async(_execute())


# ── Periyodik Zamanlama (Korundu) ─────────────────────────
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "heal-check-every-minute": {
        "task":     "tasks.project_tasks.heal_check_task",
        "schedule": 60.0,
        "options":  {"queue": "critical"},
    },
    "cleanup-memories-daily": {
        "task":     "tasks.project_tasks.cleanup_memories",
        "schedule": crontab(hour=3, minute=0),  # Her gece 03:00
        "options":  {"queue": "background"},
    },
}

@celery_app.task(name="tasks.project_tasks.send_telegram_notification_task")
def send_telegram_notification_task(event_type: str, payload: dict):
    """
    Telegram bildirimini arka planda gönderir.
    (SRE Hardening: Çakışmaları önlemek için Celery üzerinden tekil yürütme)
    """
    async def _execute():
        from apps.telegram_bot.bot import telegram_notifier
        await telegram_notifier.notify_event(event_type, payload)
    return run_async(_execute())
