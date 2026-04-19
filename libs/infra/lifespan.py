"""
libs/infra/lifespan.py — Phase 13.04
Unified startup/shutdown sequence for Sovereign AGI services.
"""
from __future__ import annotations

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from libs.db.session import init_db, close_db
from services.observability.logging import get_logger

logger = get_logger("infra.lifespan")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown of the Sovereign AGI services.
    """
    logger.info("Initializing Sovereign AGI Platform [Phase 13.04]...")

    # 1. Database Initialization
    try:
        await init_db()
        logger.info("[STARTUP] Database connection established and tables verified.")
    except Exception as e:
        logger.error(f"[STARTUP] CRITICAL: DB Init Failed: {e}", exc_info=True)
        # We continue to allow degraded mode if configured in session.py

    # 2. Sovereign Cortex & Engine Startup
    try:
        from services.orchestration.application.sovereign_cortex import get_sovereign_cortex
        cortex = get_sovereign_cortex()
        
        # Start core cognitive loops (Asynchronous startup to prevent blocking the web server)
        asyncio.create_task(cortex.start())
        logger.info("[STARTUP] SovereignCortex cognitive loops initiated in background.")
        
        # Initialize Workflow Engine & Actions
        from libs.workflow.runner import get_engine
        _ = get_engine() 
        logger.info("[STARTUP] WorkflowEngine initialized and default actions registered.")

        # 3. Job Queue In-Process Background Workers
        from services.orchestration.application.job_queue import job_queue
        if job_queue.backend_name == "inprocess":
            from libs.workflow.runner import run_project_workflow
            
            async def _project_handler(**payload):
                p_id = payload.get("db_project_id") or payload.get("project_id")
                logger.info(f"[JOB-QUEUE] EXEC: {p_id} ({payload.get('title')})")
                try:
                    await run_project_workflow(
                        project_id=p_id,
                        title=payload.get("title", "Untitled"),
                        description=payload.get("description", ""),
                        workflow_template=payload.get("workflow_template", "default"),
                        quality_profile=payload.get("quality_profile", "standard"),
                    )
                    logger.info(f"[JOB-QUEUE] SUCCESS: {p_id}")
                except Exception as ex:
                    logger.error(f"[JOB-QUEUE] FAILED: {p_id} | Error: {ex}")
                    # Note: WorkflowEngine already handles DB error marking if it crashes inside engine.execute

            async def _dummy_handler(**payload):
                logger.info(f"🔔 [JOB-QUEUE] Background task triggered (InProcess): {payload}")

            job_queue.register("run_project", _project_handler)
            job_queue.register("send_webhook", _dummy_handler)
            job_queue.register("cleanup", _dummy_handler)
            
            await job_queue.start(num_workers=4)
            logger.info("[STARTUP] In-process JobQueue workers started (Resilient Mode).")
        
        # 4. Standby Mode: PRMR Readiness Audit (Low Frequency)
        async def _prmr_audit_loop():
            from services.governance.standby_manager import StandbyManager
            logger.info("[STANDBY] PRMR Readiness Audit loop started (Interval: 15m).")
            
            while StandbyManager.is_in_standby():
                try:
                    # Run the external script logic (or imported function)
                    from prmr_readiness_audit import run_audit
                    await run_audit()
                except Exception as audit_err:
                    logger.warning(f"[STANDBY-AUDIT] Audit failed: {audit_err}")
                
                # Sleep for 15 minutes (900 seconds)
                await asyncio.sleep(900)
            
            logger.info("[STANDBY] TRIGGER DETECTED. Exiting Standby Audit Loop. Primary Initiation authorized.")

        asyncio.create_task(_prmr_audit_loop())
        logger.info("[STANDBY] System is in STANDBY MODE. Awaiting trigger: 'Hazır, PRMR-01 Faz 1’i yeniden başlat.'")

    except Exception as e:
        logger.error(f"[STARTUP] Component Init Failed: {e}", exc_info=True)

    yield

    # ── Shutdown Sequence ─────────────────────────────────────────────────────
    logger.info("Shutting down Sovereign AGI Platform...")
    
    try:
        from services.orchestration.application.sovereign_cortex import get_sovereign_cortex
        cortex = get_sovereign_cortex()
        await cortex.shutdown()
        logger.info("[SHUTDOWN] SovereignCortex stopped.")
    except Exception as e:
        logger.warning(f"[SHUTDOWN] Cortex shutdown error: {e}")

    try:
        await close_db()
        logger.info("[SHUTDOWN] Database connections closed.")
    except Exception as e:
        logger.warning(f"[SHUTDOWN] DB close error: {e}")

    logger.info("Shutdown complete.")


def register_event_listeners():
    """
    Registers global event listeners to the Domain Event Bus.
    Ensures that events like project completion or system alerts are handled centrally.
    """
    from services.orchestration.domain.events import event_bus
    from services.observability.logging import get_logger
    
    event_logger = get_logger("infra.events")

    async def _on_project_any(event):
        event_logger.info(f"[EVENT] {event.type}: {event.payload.get('project_id') or event.payload.get('id')}")

    async def _on_system_alert(event):
        event_logger.warning(f"[ALERT] {event.type}: {event.payload}")

    # Register listeners
    event_bus.on_any(_on_project_any)
    event_bus.on("system.budget_warn", _on_system_alert)
    event_bus.on("system.cascade_fail", _on_system_alert)
    
    event_logger.info("Global event listeners registered.")
