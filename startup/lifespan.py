"""
startup/lifespan.py — Uygulama yaşam döngüsü, arka plan görevleri ve event bus yapılandırması.

main.py'den çıkarılmıştır. Tüm watchdog loop'ları, event dinleyicileri
ve startup/shutdown mantığı burada yaşar.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from config import APP_ENV as _ENV
from core.orchestrator import orchestrator
from core.heal_engine import heal_engine
from core.events import event_bus
from core.job_queue import job_queue
from api.ws_manager import ws_manager
from core.reaper_service import reaper
from observability.logging import configure_logging, get_logger
from observability.metrics import metrics

logger = get_logger("startup.lifespan")


# ─── Event Bus Dinleyicileri ──────────────────────────────
async def _forward_to_ws(event):
    await ws_manager.broadcast({"event": event.type, "timestamp": event.timestamp, **event.payload})


async def _persist_event(event):
    if event.payload.get("severity") in ("critical", "warning", "resolved"):
        try:
            from db.session import AsyncSessionLocal
            from db.repository import EventLogRepository
            async with AsyncSessionLocal() as db:
                await EventLogRepository.write(
                    db,
                    event_type=event.type,
                    agent_id=event.payload.get("agent_id", "system"),
                    severity=event.payload.get("severity", "info"),
                    phase=event.payload.get("phase", ""),
                    message=event.payload.get("message", ""),
                    payload=event.payload,
                )
                await db.commit()
        except Exception as e:
            import logging
            logging.getLogger("event_bus").error(f"Event DB'ye yazılırken hata: {e}")


async def _forward_to_telegram(event):
    """Proje/ajan olaylarini Telegram'a ilet."""
    try:
        from telegram_app.bot import telegram_notifier
        await telegram_notifier.notify_event(event.type, event.payload)
    except Exception as e:
        import logging
        logging.getLogger("telegram").warning(f"Telegram bildirimi gönderilemedi: {e}")


def register_event_listeners():
    """Event bus dinleyicilerini kaydet."""
    event_bus.on_any(_forward_to_ws)
    event_bus.on_any(_persist_event)
    event_bus.on_any(_forward_to_telegram)


# ─── Watchdog Loop'ları ───────────────────────────────────
async def ceo_watchdog_loop():
    from core.ceo_engine import CEOEngine
    from core.orchestrator import orchestrator as _orch
    ceo = CEOEngine(_orch.model_orch)

    while True:
        try:
            await ceo.run_scan()
            await asyncio.sleep(300)
        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                logger.warning(f"CEO Watchdog: Database table missing. Waiting for migrations. (Error: {e})")
                await asyncio.sleep(60)
            else:
                logger.error(f"CEO Hatası: {e}", exc_info=True)
                await asyncio.sleep(60)


async def system_controller_watchdog_loop():
    """Faz 12: Sistem sağlığını ve maliyetlerini denetleyen loop."""
    from core.orchestrator import orchestrator as _orch

    agent = _orch._agents.get("system_controller")
    if not agent:
        from agents.system_controller import SystemControllerAgent
        agent = SystemControllerAgent()
        _orch._agents["system_controller"] = agent

    agent.llm = _orch.model_orch

    while True:
        try:
            out = await agent.execute(
                task_id=f"audit-{datetime.now().strftime('%Y%m%d')}",
                subtask_id=str(uuid.uuid4())[:8],
                context={"additional_context": "Periyodik Sistem Denetimi"},
            )
            severity = "info"
            if "critical" in out.summary.lower():
                severity = "critical"
            elif "degraded" in out.summary.lower():
                severity = "warning"

            await event_bus.emit(
                "system.audit",
                message=out.summary,
                severity=severity,
                agent_id="system_controller",
                payload={"parsed_audit": out.raw_output},
            )
            await asyncio.sleep(1800)
        except Exception as e:
            logger.error(f"System Controller Hatası: {e}")
            await asyncio.sleep(120)


async def memory_leak_watchdog_loop():
    """Hafıza sızıntısı (memory leak) tespit eden arka plan görevicisi."""
    try:
        import psutil
    except ImportError:
        logger.warning("psutil kurulu değil, memory_leak_watchdog devre dışı.")
        await asyncio.sleep(86400)
        return

    process = psutil.Process(os.getpid())
    history: list[float] = []

    while True:
        try:
            mem_mb = process.memory_info().rss / 1024 / 1024
            history.append(mem_mb)

            if len(history) > 10:
                history.pop(0)

            if len(history) == 10:
                is_leaking = all(history[i] <= history[i + 1] for i in range(9))
                growth_rate = (history[-1] - history[0]) / history[0] if history[0] > 0 else 0

                if is_leaking and (growth_rate > 0.15 or (history[-1] - history[0]) > 50):
                    msg = (
                        f"Olası Hafıza Sızıntısı! Bellek kullanımı sürekli artıyor: "
                        f"{history[0]:.1f}MB -> {history[-1]:.1f}MB"
                    )
                    logger.error(f"[MEMORY LEAK DETECTED] {msg}")
                    import gc
                    gc.collect()

                    await event_bus.emit(
                        "system.memory_leak_warning",
                        message=msg,
                        severity="critical",
                        agent_id="system_monitor",
                        payload={
                            "memory_mb": round(history[-1], 2),
                            "growth_rate": round(growth_rate, 2),
                            "action": "gc_collect",
                        },
                    )
                    os.environ["SYSTEM_DEGRADED_MODE"] = "true"
                    history.clear()

            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Memory Leak Watchdog Hatası: {e}")
            await asyncio.sleep(60)


async def reaper_watchdog_loop():
    """Arka planda asılı kalan (zombie) görevleri periyodik olarak temizler."""
    from datetime import timedelta
    from sqlalchemy import update, or_
    from db.models import Project, ProjectStatus
    from db.session import AsyncSessionLocal

    while True:
        try:
            async with AsyncSessionLocal() as db:
                timeout_limit = datetime.now(timezone.utc) - timedelta(hours=1)
                
                # Hem RUNNING hem de QUEUED olan ama 1 saattir güncellenmeyenleri bul
                zombie_query = (
                    update(Project)
                    .where(
                        or_(
                            Project.status == ProjectStatus.RUNNING,
                            Project.status == ProjectStatus.QUEUED
                        )
                    )
                    .where(Project.updated_at < timeout_limit)
                    .values(
                        status=ProjectStatus.ERROR,
                        error_detail="Görev zaman aşımına uğradı (Reaper tarafından temizlendi).",
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                
                res = await db.execute(zombie_query)
                await db.commit()
                
                if res.rowcount and res.rowcount > 0:
                    logger.warning(f"🧟 Reaper Watchdog: {res.rowcount} asılı görev (zombie) ERROR durumuna çekildi.")
            
            await asyncio.sleep(600)  # 10 dakikada bir çalış
        except Exception as e:
            logger.error(f"Reaper Watchdog Hatası: {e}")
            await asyncio.sleep(120)


async def system_watchdog_supervisor():
    """Arka plandaki tüm kritik denetleyicilerin hayatta kalmasını sağlar."""
    from core.improvement.gate import start_improvement_background_loop

    tasks: dict[str, Any] = {
        "ceo_watchdog": ceo_watchdog_loop,
        "sys_ctrl_watchdog": system_controller_watchdog_loop,
        "heal_engine_monitor": heal_engine.monitor_loop,
        "memory_leak_monitor": memory_leak_watchdog_loop,
        "improvement_loop": start_improvement_background_loop,
        "reaper_watchdog": reaper_watchdog_loop,
    }
    running_tasks: dict[str, asyncio.Task] = {}

    try:
        for name, func in tasks.items():
            running_tasks[name] = asyncio.create_task(func(), name=name)

        while True:
            for name, task in list(running_tasks.items()):
                if task.done():
                    try:
                        exc = task.exception()
                        logger.error(
                            f"[ERR] KRITIK: {name} watchdog'u coktu! Hata: {exc}. Yeniden baslatiliyor..."
                        )
                    except Exception:
                        logger.warning(f"[WARN] KRITIK: {name} watchdog'u coktu! Yeniden baslatiliyor...")
                    running_tasks[name] = asyncio.create_task(tasks[name](), name=name)
            await asyncio.sleep(15)
    finally:
        logger.info("Watchdog Supervisor kapanıyor, alt görevler temizleniyor...")
        for name, task in running_tasks.items():
            if not task.done():
                task.cancel()
        if running_tasks:
            await asyncio.gather(*running_tasks.values(), return_exceptions=True)


# ─── Yardımcı Fonksiyonlar ─────────────────────────────────
async def _recover_zombie_tasks():
    """Önceki oturumdan kalan 'queued' veya 'running' görevleri temizle."""
    try:
        from db.session import AsyncSessionLocal
        from db.models import Project
        from sqlalchemy import update
        async with AsyncSessionLocal() as db:
            zombie_query = (
                update(Project)
                .where(Project.status.in_(["queued", "running"]))
                .values(
                    status="error",
                    error_detail="Sistem aniden kapandı/yeniden başlatıldı. Görev yarıda kaldı (Zombi).",
                )
            )
            res = await db.execute(zombie_query)
            await db.commit()
            if res.rowcount and res.rowcount > 0:
                logger.warning(f"🧟 Zombi Temizliği: Kilitli kalan {res.rowcount} görev ERROR durumuna çekildi.")
    except Exception as e:
        logger.error(f"Zombi görev temizliği başarısız: {e}")


# ─── Lifespan Context Manager ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("AI Yazilim Sirketi V2 - Faz 3 baslatiliyor...", extra={"env": _ENV})

    # 1. Veritabanı
    db_ready = False
    try:
        from db.session import init_db
        init_db()
        logger.info("Veritabani hazir.")
        db_ready = True

        # 1.1 Reaper Service (Faz 12.1)
        await reaper.start()
    except Exception as e:
        logger.critical(f"KRITIK: DB baslatilamadi: {e}")
        if _ENV != "test":
            sys.exit(1)

    # 1.5 Zombi Görev Kurtarma
    if db_ready and _ENV != "test":
        await _recover_zombie_tasks()

    # 2. Ajan orkestrasyonu
    await orchestrator.start()

    # 3. Job queue workers
    if getattr(job_queue, "supports_registration", False):
        job_queue.register("run_project", orchestrator.run_project)
        # Faz 12.1 Hydration
        if hasattr(job_queue, "hydrate_from_db"):
            await job_queue.hydrate_from_db()

        async def _handle_self_update(**payload):
            if orchestrator.self_updater:
                return await orchestrator.self_updater.modify_system_file(**payload)
            return "Self-Updater hazir degil."

        job_queue.register("self_update", _handle_self_update)

        from config import WORKER_CONCURRENCY
        await job_queue.start(num_workers=WORKER_CONCURRENCY)
        logger.info("In-process queue aktif (handler'lar kaydedildi).")
    else:
        logger.info(
            f"Queue backend={getattr(job_queue, 'backend_name', 'unknown')} | "
            "local handler registration atlandı (supports_registration=False)."
        )

    # 4. Watchdog Supervisor
    supervisor_task = asyncio.create_task(system_watchdog_supervisor(), name="System_Watchdog_Supervisor")

    # 4.1 Agency Agents
    try:
        from core.agency.loader import agency_loader
        agency_loader.load_agents()
        logger.info(f"Agency Library: {len(agency_loader.agents)} uzman ajan yuklendi.")
    except Exception as _age_err:
        logger.warning(f"Agency Library yuklenemedi: {_age_err}")

    # 5. Self-Repair Orchestrator
    try:
        from core.repair_orchestrator import get_repair_orchestrator
        rep_orch = get_repair_orchestrator(
            model_orch=getattr(orchestrator, "model_orch", None),
            project_root=os.path.dirname(os.path.dirname(__file__)) or ".",
        )
        logger.info("Self-Repair Orchestrator hazir.")
        
        # 5.1 Hydration (Faz 12.1 Stabilizasyon)
        if db_ready and _ENV != "test":
            logger.info("Self-Repair Veri Hydration baslatiliyor...")
            from repair.memory.incident_memory import incident_memory
            from repair.ingestion.incident_ingestor import incident_ingestor
            
            # Paralel hydration
            await asyncio.gather(
                incident_memory.hydrate_from_db(),
                incident_ingestor.hydrate_from_db(),
                rep_orch.hydrate_from_db()
            )
            logger.info("Self-Repair Hydration tamamlandi.")

    except Exception as _rep_err:
        logger.warning(f"Self-Repair baslatılamadi (devam): {_rep_err}")

    # 6. Onay Kapısı → Event Bus
    try:
        from quality.approval_gate import approval_gate

        async def _notify_approval_needed(req):
            await event_bus.emit(
                "approval.needed",
                request_id=req.id,
                operation=req.operation,
                description=req.description,
                risk_level=req.risk_level,
                severity="warning",
                agent_id=req.requested_by,
                phase="approval",
                message=f"Onay Bekleniyor: {req.operation} ({req.description[:50]}...)",
            )

        approval_gate.add_notifier(_notify_approval_needed)
        logger.info("Onay Kapısı bildirimleri aktif edildi.")
    except Exception as _gate_err:
        logger.warning(f"Onay Kapısı bildirim bağlantısı başarısız: {_gate_err}")

    # Degrade Mode Visibility
    from db.session import is_db_available
    db_ok = await is_db_available()
    h_score = heal_engine.system_health_score() if hasattr(heal_engine, "system_health_score") else 1.0

    if not db_ok or h_score < 0.8:
        await event_bus.emit(
            "system.degraded",
            message=f"Sistem kısıtlı modda (degraded) baslatildi. DB: {'OK' if db_ok else 'HATA'}, Health: {h_score}",
            severity="warning",
            agent_id="system",
            phase="startup",
        )

    await event_bus.emit("system.started", message="Sistem hazir.", severity="info", agent_id="system", phase="startup")

    yield  # ← Uygulama çalışıyor

    logger.info("Sistem kapatiliyor...")
    supervisor_task.cancel()
    try:
        await asyncio.wait_for(supervisor_task, timeout=5)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    await reaper.stop()
    await job_queue.stop()
    await orchestrator.shutdown()
    try:
        await event_bus.shutdown()
    except Exception:
        pass
    logger.info("Temiz kapanış tamamlandi.")
