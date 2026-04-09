"""
startup/lifespan.py â€” Uygulama yaÅŸam dÃ¶ngÃ¼sÃ¼, arka plan gÃ¶revleri ve event bus yapÄ±landÄ±rmasÄ±.

main.py'den Ã§Ä±karÄ±lmÄ±ÅŸtÄ±r. TÃ¼m watchdog loop'larÄ±, event dinleyicileri
ve startup/shutdown mantÄ±ÄŸÄ± burada yaÅŸar.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from config import APP_ENV as _ENV
from packages.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
from packages.orchestration.agi.governance.resilience_agent import resilience_agent
from packages.healing.application.heal_engine import heal_engine
from packages.orchestration.domain.events import event_bus
from packages.orchestration.application.job_queue import job_queue
from apps.api.support.ws_manager import ws_manager
from packages.repair_engine.reaper_service import reaper
from packages.observability.logging import configure_logging, get_logger
from packages.observability.metrics import metrics

logger = get_logger("startup.lifespan")


# â”€â”€â”€ Event Bus Dinleyicileri â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _forward_to_ws(event):
    await ws_manager.broadcast({"event": event.type, "timestamp": event.timestamp, **event.payload})


async def _persist_event(event):
    if event.payload.get("severity") in ("critical", "warning", "resolved"):
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repositories.repository import EventLogRepository
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
            logging.getLogger("event_bus").error(f"Event DB'ye yazÄ±lÄ±rken hata: {e}")


async def _forward_to_telegram(event):
    """Proje/ajan olaylarini Telegram'a ilet."""
    try:
        from telegram_app.bot import telegram_notifier
        await telegram_notifier.notify_event(event.type, event.payload)
    except Exception as e:
        import logging
        logging.getLogger("telegram").warning(f"Telegram bildirimi gÃ¶nderilemedi: {e}")


def register_event_listeners():
    """Event bus dinleyicilerini kaydet."""
    event_bus.on_any(_forward_to_ws)
    event_bus.on_any(_persist_event)
    event_bus.on_any(_forward_to_telegram)


# â”€â”€â”€ Watchdog Loop'larÄ± â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def autonomous_metabolism_loop():
    """
    Faz 30: BirleÅŸik BiliÅŸsel Metabolizma DÃ¶ngÃ¼sÃ¼.
    AyrÄ± ayrÄ± Ã§alÄ±ÅŸan watchdog'larÄ± tek bir dÃ¶ngÃ¼de, kendi periyotlarÄ±na gÃ¶re yÃ¶netir.
    Bundan sonra 'AutonomousMetabolismLoop' (AML) olarak anÄ±lacaktÄ±r.
    """
    from packages.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as _orch
    from packages.orchestration.ceo.engine import CEOEngine
    from packages.orchestration.agi.monitoring.token_budgeter import token_budgeter
    from packages.orchestration.agi.cognitive.evolution_engine import evolution_engine
    from packages.orchestration.agi.cognitive.policy_evolution import start_policy_evolution_loop
    from packages.orchestration.agi.cognitive.consolidator import start_consolidation_loop
    from packages.orchestration.agi.cognitive.metacognitive_auditor import start_reflection_loop
    from packages.orchestration.agi.cognitive.synapse_stabilizer import start_synapse_stabilization_loop
    
    ceo = CEOEngine(_orch.model_orch)
    
    # Periyotlar (Saniye)
    PERIODS = {
        "ceo": 300,
        "self_governor": 1800,
        "reaper": 600,
        "consolidation": 3600,
        "reflection": 7200,
        "stabilization": 3600 * 4,
        "self_audit": 3600 * 24,   # [FIX-7] 24 saatte bir Ã¶z-denetim
        "evolution": 600,          # 10 dakikada bir otonom evrim
        "dream": 14400,            # Phase 46: 4 saatte bir 'Dream' (Wisdom Consolidation)
    }

    
    last_runs = {k: 0.0 for k in PERIODS}
    
    logger.info("[AML] Otonom Metabolizma DÃ¶ngÃ¼sÃ¼ baÅŸlatÄ±ldÄ±.")
    
    while True:
        now = asyncio.get_event_loop().time()
        
        try:
            # 1. CEO Scan (High Priority)
            if now - last_runs["ceo"] >= PERIODS["ceo"]:
                try:
                    # Faz 12.1: Startup blokajini onlemek icin background task olarak calistir
                    asyncio.create_task(ceo.run_scan())
                except Exception as e:
                    logger.error(f"[AML] CEO Scan trigger failed: {e}")
                last_runs["ceo"] = now

            # 1.1 Sovereign Evolution (Reflective Reasoning)
            if now - last_runs["evolution"] >= PERIODS["evolution"]:
                try:
                    await evolution_engine.run_evolution_cycle()
                except Exception as e:
                    logger.error(f"[AML] Evolution cycle failed: {e}")
                last_runs["evolution"] = now

            # 2. Reaper (Resource Management)
            if now - last_runs["reaper"] >= PERIODS["reaper"]:
                try:
                    await _reaper_sync_action()
                except Exception as e:
                    logger.error(f"[AML] Reaper action failed: {e}")
                last_runs["reaper"] = now

            # 3. Self-Governor (Governance)
            if now - last_runs["self_governor"] >= PERIODS["self_governor"]:
                try:
                    await _self_governor_sync_action(_orch)
                except Exception as e:
                    logger.error(f"[AML] Self-Governor action failed: {e}")
                last_runs["self_governor"] = now
                
            # 4. Cognitive Tasks (Low Priority - Only if budget is healthy)
            health = await token_budgeter.check_health()
            if health["health_score"] > 0.6:
                if now - last_runs["consolidation"] >= PERIODS["consolidation"]:
                    try:
                        from packages.orchestration.agi.cognitive.consolidator import consolidator
                        await consolidator.run_cycle()
                    except Exception as e:
                        logger.error(f"[AML] Consolidation failed: {e}")
                    last_runs["consolidation"] = now
                
                if now - last_runs["reflection"] >= PERIODS["reflection"]:
                    try:
                        from packages.orchestration.agi.cognitive.reflection_cortex import reflection_cortex
                        await reflection_cortex.run_reflection_cycle()
                    except Exception as e:
                        logger.error(f"[AML] Reflection failed: {e}")
                    last_runs["reflection"] = now

                # 5. Self-Audit [FIX-7] â€” 24 saatte bir LLM tabanlÄ± kod analizi
                if now - last_runs["self_audit"] >= PERIODS["self_audit"]:
                    try:
                        from packages.orchestration.agi.cognitive.self_audit import self_audit
                        await self_audit.run_cleanup()
                    except Exception as _sa_err:
                        logger.warning(f"[AML] Self-Audit hatasÄ±: {_sa_err}")
                    last_runs["self_audit"] = now
                
                # Phase 46: System Dream (Wisdom Synthesis)
                if now - last_runs["dream"] >= PERIODS["dream"]:
                    try:
                        logger.info("[AML] Periyodik Dream Cycle (BilinÃ§altÄ± Konsolidasyon) kuyruÄŸa ekleniyor...")
                        await job_queue.enqueue("system_dream")
                    except Exception as _dr_err:
                        logger.warning(f"[AML] Dream tetikleme hatasÄ±: {_dr_err}")
                    last_runs["dream"] = now

        except Exception as e:
            logger.error(f"[AML] DÃ¶ngÃ¼ hatasÄ±: {e}")
        
        await asyncio.sleep(30) # Metabolizma hÄ±zÄ±

async def _reaper_sync_action():
    from sqlalchemy import update, or_
    from packages.persistence.models import Project, ProjectStatus
    from packages.persistence.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        timeout_limit = datetime.now(timezone.utc) - timedelta(hours=1)
        zombie_query = update(Project).where(
            or_(Project.status == ProjectStatus.RUNNING, Project.status == ProjectStatus.QUEUED)
        ).where(Project.updated_at < timeout_limit).values(
            status=ProjectStatus.ERROR,
            error_detail="GÃ¶rev zaman aÅŸÄ±mÄ± (Timeout) nedeniyle durduruldu.",
            updated_at=datetime.now(timezone.utc)
        )
        res = await db.execute(zombie_query)
        await db.commit()
        if res.rowcount > 0:
            logger.warning(f"[AML] Reaper: {res.rowcount} zombi temizlendi.")

async def _self_governor_sync_action(orch):
    agent = orch._agents.get("self_governor")
    if not agent: return
    audit_id = f"aml-audit-{uuid.uuid4().hex[:8]}"
    out = await agent.execute(
        task_id=audit_id,
        subtask_id="aml-sub",
        context={"requirements": "AML Periyodik Denetim"}
    )
    await event_bus.emit("system.audit", message=out.summary, severity="info", agent_id="self_governor")

async def system_watchdog_supervisor():
    """Arka plandaki kritik servislerin ve metabolizmanÄ±n hayatta kalmasÄ±nÄ± saÄŸlar."""
    from packages.observability.memory_governor import memory_governor
    
    tasks: dict[str, Any] = {
        "metabolism_loop": autonomous_metabolism_loop,
        "memory_governor": memory_governor.monitor_loop,
        "heal_engine_monitor": heal_engine.monitor_loop,
    }
    running_tasks: dict[str, asyncio.Task] = {}

    try:
        for name, func in tasks.items():
            running_tasks[name] = asyncio.create_task(func(), name=name)

        while True:
            for name, task in list(running_tasks.items()):
                if task.done():
                    logger.error(f"[AML-SUPERVISOR] {name} Ã§Ã¶ktÃ¼! Yeniden baÅŸlatÄ±lÄ±yor...")
                    running_tasks[name] = asyncio.create_task(tasks[name](), name=name)
            await asyncio.sleep(20)
    finally:
        for task in running_tasks.values():
            if not task.done(): task.cancel()


# â”€â”€â”€ YardÄ±mcÄ± Fonksiyonlar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _analyze_interrupted_tasks():
    """Ã–nceki oturumdan kalan 'queued' veya 'running' gÃ¶revleri 'INTERRUPTED' durumuna Ã§ek."""
    try:
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.models import Project, ProjectStatus
        from sqlalchemy import update
        async with AsyncSessionLocal() as db:
            interrupted_query = (
                update(Project)
                .where(Project.status.in_([ProjectStatus.QUEUED, ProjectStatus.RUNNING]))
                .values(
                    status=ProjectStatus.INTERRUPTED,
                    error_detail="Sistem kesintiye uÄŸradÄ±. Otonom dayanÄ±klÄ±lÄ±k (Resilience) analizi bekleniyor.",
                )
            )
            res = await db.execute(interrupted_query)
            await db.commit()
            if res.rowcount and res.rowcount > 0:
                logger.warning(f"Kesinti Analizi: {res.rowcount} gorev INTERRUPTED durumuna cekildi.")
    except Exception as e:
        logger.error(f"Kesinti analizi baÅŸarÄ±sÄ±z: {e}")


# â”€â”€â”€ Lifespan Context Manager â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("AI Yazilim Sirketi V2 - Faz 3 baslatiliyor...", extra={"env": _ENV})

    # 1. VeritabanÄ±
    db_ready = False
    try:
        from packages.persistence.session import init_db
        await init_db()
        # 1.1 Event Bus Bridging (Phase 12.1 Refactor)
        register_event_listeners()
        logger.info("Event Bus dinleyicileri (WS/DB/Telegram) aktif edildi.")

        # 1.2 Reaper Service (Faz 12.1)
        await reaper.start()
    except Exception as e:
        logger.critical(f"KRITIK: DB baslatilamadi: {e}")
        if _ENV != "test":
            sys.exit(1)

    # 1.5 Kesinti Analizi ve Kurtarma HazÄ±rlÄ±ÄŸÄ±
    if db_ready and _ENV != "test":
        await _analyze_interrupted_tasks()

    # 2. Ajan orkestrasyonu
    await orchestrator.start()
    
    # 2.5 Resilience Agent (Otonom Kurtarma)
    await resilience_agent.start()

    # 3. Job queue workers
    if getattr(job_queue, "supports_registration", False):
        # Nexus iÃ§in coordinate_goal'u task_write/job_queue beklediÄŸi run_project formatÄ±na baÄŸla
        async def _run_project_wrapper(**payload):
            return await orchestrator.coordinate_goal(
                title=payload.get("title", "Unnamed Goal"),
                description=payload.get("description", ""),
                project_id=payload.get("db_project_id", ""),
                workflow_template=payload.get("workflow_template"),
                quality_profile=payload.get("quality_profile"),
                acceptance_criteria=payload.get("acceptance_criteria"),
                execution_context=payload.get("execution_context")
            )

        job_queue.register("run_project", _run_project_wrapper)

        # Faz 12.1: DeerFlow Handlers (Real Bridge Integration)
        async def _run_deerflow_wrapper(**payload):
            try:
                from packages.integrations.deerflow_bridge import DeerFlowBridgeClient
                client = DeerFlowBridgeClient()
                
                # Payload mapping
                thread_id = payload.get("db_project_id") or payload.get("job_id") or str(uuid.uuid4())
                prompt = payload.get("description") or payload.get("title") or "DeerFlow Task"
                
                logger.info(f"[DEERFLOW] Routing task to bridge (thread={thread_id})")
                res = await client.run(thread_id=thread_id, prompt=prompt)
                
                if res.get("status") == "error":
                     logger.warning(f"[DEERFLOW] Bridge error, falling back: {res.get('message')}")
                     return await _run_project_wrapper(**payload)
                
                return res
            except Exception as e:
                logger.error(f"[DEERFLOW] Bridge integration failed: {e}. Falling back to internal engine.")
                return await _run_project_wrapper(**payload)

        for df_task in ["deerflow_run", "deerflow_plan", "deerflow_research", "deerflow_review", "deerflow_recovery"]:
            job_queue.register(df_task, _run_deerflow_wrapper)
        # Faz 12.1 Hydration
        if hasattr(job_queue, "hydrate_from_db"):
            await job_queue.hydrate_from_db()

        async def _handle_self_update(**payload):
            if orchestrator.self_updater:
                return await orchestrator.self_updater.modify_system_file(**payload)
            return "Self-Updater hazir degil."

        job_queue.register("self_update", _handle_self_update)
        
        # Phase 46: Subconscious Dream Handler
        async def _run_dream_cycle(**payload):
            from packages.orchestration.agi.cognitive.subconscious_cortex_45 import subconscious_cortex_45
            from packages.persistence.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                return await subconscious_cortex_45.dream(db)
        
        job_queue.register("system_dream", _run_dream_cycle)

        from config import WORKER_CONCURRENCY
        await job_queue.start(num_workers=WORKER_CONCURRENCY)
        logger.info("In-process queue aktif (handler'lar kaydedildi).")
    else:
        logger.info(
            f"Queue backend={getattr(job_queue, 'backend_name', 'unknown')} | "
            "local handler registration atlandÄ± (supports_registration=False)."
        )

    # 4. Watchdog Supervisor
    supervisor_task = asyncio.create_task(system_watchdog_supervisor(), name="System_Watchdog_Supervisor")

    # 4.1 Agency Agents
    try:
        from packages.orchestration.agency.loader import agency_loader
        agency_loader.load_agents()
        logger.info(f"Agency Library: {len(agency_loader.agents)} uzman ajan yuklendi.")
    except Exception as _age_err:
        logger.warning(f"Agency Library yuklenemedi: {_age_err}")

    # 5. Self-Repair Orchestrator
    try:
        from packages.repair_engine.application.orchestrator import get_repair_orchestrator
        rep_orch = get_repair_orchestrator(
            model_orch=getattr(orchestrator, "model_orch", None),
            project_root=os.path.dirname(os.path.dirname(__file__)) or ".",
        )
        logger.info("Self-Repair Orchestrator hazir.")
        
        # 5.1 Hydration (Faz 12.1 Stabilizasyon)
        if db_ready and _ENV != "test":
            logger.info("Self-Repair Veri Hydration baslatiliyor...")
            from packages.repair_engine.memory.incident_memory import incident_memory
            from packages.repair_engine.ingestion.incident_ingestor import incident_ingestor
            
            # Paralel hydration
            await asyncio.gather(
                incident_memory.hydrate_from_db(),
                incident_ingestor.hydrate_from_db(),
                rep_orch.hydrate_from_db()
            )
            logger.info("Self-Repair Hydration tamamlandi.")

    except Exception as _rep_err:
        logger.warning(f"Self-Repair baslatÄ±lamadi (devam): {_rep_err}")

    # 6. Onay KapÄ±sÄ± â†’ Event Bus
    try:
        from packages.quality_assurance.approval_gate import approval_gate

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
        logger.info("Onay KapÄ±sÄ± bildirimleri aktif edildi.")
    except Exception as _gate_err:
        logger.warning(f"Onay KapÄ±sÄ± bildirim baÄŸlantÄ±sÄ± baÅŸarÄ±sÄ±z: {_gate_err}")

    # Degrade Mode Visibility
    from packages.persistence.session import is_db_available
    db_ok = await is_db_available()
    h_score = heal_engine.system_health_score() if hasattr(heal_engine, "system_health_score") else 1.0

    if not db_ok or h_score < 0.8:
        await event_bus.emit(
            "system.degraded",
            message=f"Sistem kÄ±sÄ±tlÄ± modda (degraded) baslatildi. DB: {'OK' if db_ok else 'HATA'}, Health: {h_score}",
            severity="warning",
            agent_id="system",
            phase="startup",
        )

    await event_bus.emit("system.started", message="Sistem hazir.", severity="info", agent_id="system", phase="startup")

    # 7. Affective Core Hydration [FIX-4] â€” Ã–nceki duygusal baÄŸlamÄ± yÃ¼kle
    if db_ready and _ENV != "test":
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.orchestration.agi.consciousness.affective_core import affective_core
            async with AsyncSessionLocal() as db:
                restored = await affective_core.load_state(db)
            if restored:
                logger.info(f"[STARTUP] Affective Core hydrated. Mood: {affective_core.get_current_mood()}")
        except Exception as _aff_err:
            logger.warning(f"[STARTUP] Affective Core hydration atlandÄ±: {_aff_err}")

    # 8. GlobalWorkspace â€” Ä°lk BilinÃ§ YayÄ±nÄ± [FIX-6]
    try:
        from packages.orchestration.agi.consciousness.global_workspace import global_workspace
        from packages.persistence.session import is_db_available as _is_db_ok
        db_status = "nominal" if await _is_db_ok() else "degraded"
        global_workspace.broadcast(
            layer_name="startup",
            thought={"event": "system_initialized", "db_status": db_status, "env": _ENV},
            importance=1.0
        )
        logger.info("[STARTUP] GlobalWorkspace ilk yayÄ±n yapÄ±ldÄ±.")
    except Exception as _gw_err:
        logger.warning(f"[STARTUP] GlobalWorkspace broadcast atlandÄ±: {_gw_err}")


    yield  # â† Uygulama Ã§alÄ±ÅŸÄ±yor

    logger.info("Sistem kapatiliyor...")
    supervisor_task.cancel()
    try:
        await asyncio.wait_for(supervisor_task, timeout=5)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    await reaper.stop()
    await job_queue.stop()
    try:
        await orchestrator.shutdown()
    except Exception:
        pass
    try:
        await event_bus.shutdown()
    except Exception:
        pass
    logger.info("Temiz kapanÄ±ÅŸ tamamlandi.")

