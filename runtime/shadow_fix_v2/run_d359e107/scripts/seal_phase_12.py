import os
import sys

# Project root setup
_root = "E:/ai_company_faz12.1"
if _root not in sys.path:
    sys.path.append(_root)

# 1. Force environment
os.environ['DATABASE_URL'] = 'sqlite:///E:/ai_company_faz12.1/runtime/data/cortex_local.db'
os.environ['APP_ENV'] = 'development'

# 2. Patch ALL possible locations
import libs.config
libs.config.DATABASE_URL = os.environ['DATABASE_URL']

import libs.db.session
libs.db.session.DATABASE_URL = os.environ['DATABASE_URL']
# Also reset the engines if they were already created
libs.db.session._sync_engine = None
libs.db.session._engine = None

from libs.db.session import SessionLocal
from libs.db.models.governance_models import GovernanceProofEventRecord
from services.governance.proof_fabric import ProofFabric
from sqlalchemy import func, select
from services.observability.logging import get_logger

logger = get_logger("proof.manual_seal")

def seal_phase_12_snapshot():
    """Manual seal of Phase 12 completion state using multi-layer patched session."""
    with SessionLocal() as db:
        try:
            # Verify engine
            engine_url = str(db.get_bind().url)
            logger.info(f"Targeting Engine: {engine_url}")
            
            if "postgresql" in engine_url:
                 logger.error("FATAL: Still targeting PostgreSQL. Aborting to avoid connection errors.")
                 return

            # Get Max Index
            max_idx = db.scalar(select(func.max(GovernanceProofEventRecord.chain_index)))
            if max_idx is None:
                logger.warning("No events to seal.")
                return

            fabric = ProofFabric(db)
            logger.info(f"Sealing Phase 12 events from 0 to {max_idx}...")
            
            snapshot = fabric.seal_snapshot(
                "PHASE_12_FINAL_SNAP_20260427",
                0,
                max_idx,
                "SYSTEM_CLOSE"
            )
            logger.info(f"OK: Phase 12 Sealed. Snapshot ID: {snapshot.id}, Merkle Root: {snapshot.merkle_root}")
            
        except Exception as e:
            logger.error(f"Failed to seal snapshot: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    seal_phase_12_snapshot()
