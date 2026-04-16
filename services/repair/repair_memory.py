import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from libs.db.models.core_models import SovereignEvidence
from libs.db.session import AsyncSessionLocal

logger = logging.getLogger("repair.memory")

class RepairOutcome(BaseModel):
    """Historical record of a repair attempt."""
    incident_id: str
    scenario_id: Optional[str] = None
    applied_strategy: str
    outcome: str  # SUCCESS, FAILED, PARTIAL
    failure_reason: Optional[str] = None
    mttr_ms: float
    cost_delta: float
    timestamp: datetime = datetime.now()

class RepairMemory:
    """Manages persistent storage and retrieval of repair histories."""
    
    def __init__(self):
        pass

    async def record_outcome(self, outcome: RepairOutcome):
        """Persists a repair outcome to the SovereignEvidence ledger."""
        logger.info(f"Recording Repair Memory for Incident: {outcome.incident_id}")
        
        payload_data = outcome.dict()
        payload_data["source_component"] = "RepairEngine"

        evidence = SovereignEvidence(
            evidence_type="REPAIR_OUTCOME",
            payload=payload_data,
            severity="info" if outcome.outcome == "SUCCESS" else "warning",
            created_at=outcome.timestamp
        )
        
        try:
            async with AsyncSessionLocal() as db:
                db.add(evidence)
                await db.commit()
                logger.info("Repair outcome successfully persisted to memory.")
        except Exception as e:
            logger.error(f"Failed to persist repair memory: {e}")

    async def get_performance_stats(self, strategy_name: str) -> Dict[str, Any]:
        """Retrieves success rates and cost history for a specific strategy."""
        # Query database for historical trends (Placeholder for Phase 28 Stage 4)
        return {
            "strategy": strategy_name,
            "success_rate": 0.85,  # Mock for initial setup
            "avg_cost": 45.0,
            "recurrence_prevention_factor": 0.72
        }

    def close(self):
        pass
