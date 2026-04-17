"""
Sovereign AGI — verify_phase29.py
Verification suite for Autonomous Governance Evolution.
"""

import asyncio
import uuid
from typing import Dict, Any

from libs.db.session import async_session_factory
from libs.db.models.lineage_models import DecisionLineage
from services.governance.lineage_service import LineageService
from services.governance.policy_logic_sync import PolicyLogicSync
from services.observability.logging import get_logger

logger = get_logger("verify.phase29")

async def verify_lineage_logging():
    logger.info("Verifying Lineage Logging...")
    decision = await LineageService.log_decision(
        decision_type="TEST_DECISION",
        component_name="VerificationSuite",
        rationale="Testing Phase 29 lineage tracking",
        trigger_event={"status": "testing"}
    )
    assert decision.id is not None
    assert decision.decision_type == "TEST_DECISION"
    logger.info(f"✓ Lineage Logging Verified (ID: {decision.id})")

async def verify_policy_sync():
    logger.info("Verifying Policy Logic Sync...")
    audit = await PolicyLogicSync.audit_consistency()
    assert audit["status"] == "CONSISTENT"
    logger.info("✓ Policy Logic Sync Verified")

async def run_all_checks():
    logger.info("=== STARTING PHASE 29 VERIFICATION ===")
    try:
        await verify_lineage_logging()
        await verify_policy_sync()
        logger.info("=== PHASE 29 VERIFICATION COMPLETED SUCCESSFULLY ===")
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_all_checks())
