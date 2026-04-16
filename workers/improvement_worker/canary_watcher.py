import asyncio
import logging
from datetime import datetime, timezone
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SystemImprovement
from services.improve.rollout_manager import RolloutManager
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("canary_watcher")

async def run_canary_watcher():
    """
    Phase 16: Monitors active canary patches and promotes/rolls them back based on telemetry.
    """
    logger.info("🚀 Canary Watcher started (Phase 16 Observation Loop)")
    
    while True:
        try:
            async with AsyncSessionLocal() as session:
                # 1. Fetch all active canaries
                stmt = select(SystemImprovement).where(SystemImprovement.status == "canary")
                result = await session.execute(stmt)
                canaries = result.scalars().all()
                
                if canaries:
                    logger.info(f"Checking {len(canaries)} active canaries...")
                    # We need a rollout manager for each check
                    # Root path might need to be resolved correctly
                    project_root = "." # In production worker, this is the CWD
                    
                    rollout_mgr = RolloutManager(session, project_root)
                    
                    for patch in canaries:
                        await rollout_mgr.verify_and_promote(patch.id)
                
            # Sleep for 1 minute between checks
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in Canary Watcher: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_canary_watcher())
