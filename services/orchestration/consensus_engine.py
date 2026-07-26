"""
Sovereign AGI — Phase 27
services/orchestration/consensus_engine.py
Autonomous Cross-Region Role Arbitration & High Availability.
"""
import asyncio
import uuid
from typing import Optional
from libs.mesh.state_fabric import state_fabric
from services.observability.logging import get_logger

logger = get_logger("mesh.consensus")

class ConsensusEngine:
    def __init__(self, region_id: str):
        self.region_id = region_id
        self.current_role = "standby" # default
        self._is_running = False
        self._priority_score = 100 # Default score

    async def start_consensus_loop(self):
        """Main HA loop: updates health and arbitrates leadership."""
        self._is_running = True
        logger.info(f"ConsensusEngine: Started for region {self.region_id}")
        
        while self._is_running:
            try:
                await self._refresh_consensus()
            except Exception as e:
                logger.error(f"Consensus loop error: {e}")
            await asyncio.sleep(5)

    async def _refresh_consensus(self):
        # 1. Update our regional status in the fabric
        status = {
            "role": self.current_role,
            "status": "healthy",
            "priority": self._priority_score,
            "tasks_handled": 0 # Replace with real metric
        }
        await state_fabric.put_region_state(self.region_id, status)
        
        # 2. Check for Global Leader
        mesh_view = await state_fabric.get_mesh_view()
        primary_exists = False
        for rid, data in mesh_view.items():
            if data.get("role") == "primary":
                # Check if leader is stale (heartbeat > 15s)
                import time
                if time.time() - data.get("last_seen", 0) < 15:
                    primary_exists = True
                    break
        
        # 3. Attempt Leadership if no primary
        if not primary_exists:
            logger.warning(f"ConsensusEngine: No primary detected in mesh. Region {self.region_id} attempting leadership...")
            if await state_fabric.acquire_global_lock("mesh_primary_election", timeout=20):
                self.current_role = "primary"
                logger.info(f"ConsensusEngine: REGION {self.region_id} IS NOW PRIMARY.")
                # Update status immediately
                status["role"] = "primary"
                await state_fabric.put_region_state(self.region_id, status)
            else:
                self.current_role = "standby"
        
        # 4. If we are Primary, ensure we keep the lock refreshed (implicit by lock timeout > sleep)
        
    def set_priority(self, score: int):
        self._priority_score = score

# Singleton management usually handled by runner, but we provide factory
def get_consensus_engine(region_id: str) -> ConsensusEngine:
    return ConsensusEngine(region_id)
