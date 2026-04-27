import asyncio
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from libs.db.session import SessionLocal
from services.governance.proof_fabric import ProofFabric
from services.observability.logging import get_logger
from libs.db.repositories.governance_proof_repository import GovernanceProofEventRepo, GovernanceProofSnapshotRepo

logger = get_logger("governance.proof.scheduler")

class ProofSnapshotScheduler:
    def __init__(self):
        self.running = False

    async def start(self):
        self.running = True
        logger.info("Proof Snapshot Scheduler started.")
        while self.running:
            try:
                await self.run_snapshot_cycle()
            except Exception as e:
                logger.error(f"Snapshot cycle failed: {str(e)}")
            
            # Run every 24 hours (or as configured)
            await asyncio.sleep(86400)

    async def run_snapshot_cycle(self):
        """
        Determines the next chain range to seal and triggers the seal.
        """
        with SessionLocal() as db:
            event_repo = GovernanceProofEventRepo(db)
            snap_repo = GovernanceProofSnapshotRepo(db)
            fabric = ProofFabric(db)
            
            last_snap = snap_repo.list_snapshots(limit=1)
            start_idx = (last_snap[0].end_chain_index + 1) if last_snap else 0
            
            last_event = event_repo.get_last_event()
            if not last_event or last_event.chain_index < start_idx:
                logger.info("No new events to seal.")
                return
                
            end_idx = last_event.chain_index
            
            logger.info(f"Sealing snapshot from index {start_idx} to {end_idx}...")
            snap_name = f"DAILY_SEAL_{datetime.now().strftime('%Y%m%d')}"
            
            fabric.seal_snapshot(snap_name, start_idx, end_idx, actor="SYSTEM_SCHEDULER")
            logger.info(f"Snapshot {snap_name} sealed successfully.")

    def stop(self):
        self.running = False
