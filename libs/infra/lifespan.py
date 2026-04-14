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
