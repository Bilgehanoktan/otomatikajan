import asyncio
import logging
from sqlalchemy import text
from db.session import _get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NAS_Migration")

async def migrate():
    """Add agent_role column to llm_cost_logs if not already there."""
    engine = _get_engine()
    if engine is None:
        logger.error("Database engine not available.")
        return

    logger.info("Checking schema for llm_cost_logs...")
    
    async with engine.begin() as conn:
        # P0: Postgres-specific "COLUMN IF NOT EXISTS" logic
        try:
            await conn.execute(text("ALTER TABLE llm_cost_logs ADD COLUMN IF NOT EXISTS agent_role VARCHAR(50)"))
            logger.info("OK: agent_role column is active on llm_cost_logs.")
        except Exception as e:
            logger.error(f"Migration error: {e}")
            
        # P1: Index for Performance (Phase 64 Requirement)
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_llm_cost_logs_role ON llm_cost_logs(agent_role)"))
            logger.info("OK: Index idx_llm_cost_logs_role is active.")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
