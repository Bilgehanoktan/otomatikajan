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
        
        # Start core cognitive loops
        await cortex.start()
        logger.info("[STARTUP] SovereignCortex cognitive loops started.")
        
        # Initialize Workflow Engine & Actions
        from libs.workflow.runner import get_engine
        _ = get_engine() 
        logger.info("[STARTUP] WorkflowEngine initialized and default actions registered.")
        
    except Exception as e:
        logger.error(f"[STARTUP] Component Init Failed: {e}", exc_info=True)

    yield

    # ── Shutdown Sequence ─────────────────────────────────────────────────────
    logger.info("Shutting down Sovereign AGI Platform...")
    
    try:
        from services.orchestration.application.sovereign_cortex import get_sovereign_cortex
        cortex = get_sovereign_cortex()
        await cortex.stop()
        logger.info("[SHUTDOWN] SovereignCortex stopped.")
    except Exception as e:
        logger.warning(f"[SHUTDOWN] Cortex stop error: {e}")

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
