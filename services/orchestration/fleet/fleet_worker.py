import asyncio
import time
from services.governance.fleet_governor import FleetGovernor
from services.governance.fleet_observability import FleetObservability
from libs.db.session import SessionLocal
from services.observability.logging import get_logger

logger = get_logger("fleet.worker")

async def run_fleet_governance_cycle():
    """Periodically evaluates fleet health and applies autonomous decisions."""
    while True:
        try:
            with SessionLocal() as db:
                governor = FleetGovernor(db)
                obs = FleetObservability(db)
                
                # 1. Collect Metrics
                metrics = obs.aggregate_fleet_metrics()
                logger.info(f"[FleetWorker] Health Check: {metrics['agents']['busy_ratio']*100:.1f}% busy")
                
                # 2. Evaluate Health
                results = governor.evaluate_fleet_health()
                
                # 3. Apply Decisions
                for decision in results.get("decisions", []):
                    logger.warning(f"[FleetWorker] Applying Decision: {decision['action']} for {decision['reason']}")
                    governor.apply_decision(decision)
                    
        except Exception as e:
            logger.error(f"[FleetWorker] Cycle failed: {e}")
            
        await asyncio.sleep(60) # Run every minute

if __name__ == "__main__":
    asyncio.run(run_fleet_governance_cycle())
