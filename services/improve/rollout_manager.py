from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime, timezone, timedelta
import logging
from uuid import UUID
from pathlib import Path
from sqlalchemy import select, and_
from libs.db.models.core_models import SystemImprovement, OperationalIncident, Project
from services.orchestration.application.self_updater import SelfUpdater
from services.orchestration.application.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)

class RolloutManager:
    CANARY_DURATION_MINUTES = 15

    def __init__(self, db_session, project_root: str, model_orch=None):
        self.db = db_session
        self.project_root = project_root
        self.model_orch = model_orch
        self.updater = SelfUpdater(model_orch, project_root) if model_orch else None
        self.rb_mgr = RollbackManager(project_root)

    def set_updater(self, updater: SelfUpdater):
        self.updater = updater

    async def apply_canary(self, improvement_id: UUID) -> bool:
        """
        Applies the patch as a canary and records the snapshot for potential rollback.
        """
        patch = await self.db.get(SystemImprovement, improvement_id)
        if not patch:
            raise ValueError(f"Improvement {improvement_id} not found")

        logger.info(f"🚀 Initializing CANARY for {patch.target_file} (Risk: {patch.risk_score})")
        
        # 1. Ensure we have an updater
        if not self.updater:
            logger.error("SelfUpdater not configured in RolloutManager")
            return False

        # 2. Create a snapshot BEFORE applying
        snapshot_tag = self.rb_mgr.create_snapshot(f"canary_{patch.id.hex[:8]}")

        # 3. Apply the patch
        # Note: modify_system_file handles its own internal immediate rollback,
        # but here we are establishing an OLDER baseline for Phase 16 long-term canary.
        try:
            result_msg = await self.updater.modify_system_file(patch.target_file, patch.instruction)
            
            if "Başarılı" not in result_msg:
                logger.error(f"Canary application failed at update stage: {result_msg}")
                patch.status = "rejected_verification"
                await self.db.commit()
                return False

            # 4. Successful update, set canary window
            canary_until = datetime.now(timezone.utc) + timedelta(minutes=self.CANARY_DURATION_MINUTES)
            
            rollout_meta = patch.test_results or {}
            rollout_meta["rollout_meta"] = {
                "canary_start": datetime.now(timezone.utc).isoformat(),
                "canary_until": canary_until.isoformat(),
                "snapshot_tag": snapshot_tag,
                "status": "canary_active"
            }
            patch.test_results = rollout_meta
            patch.status = "canary"
            patch.applied_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            logger.info(f"✅ CANARY ACTIVE until {canary_until}. Snapshot: {snapshot_tag}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply canary hardware: {e}")
            patch.status = "failed"
            await self.db.commit()
            return False

    async def verify_and_promote(self, improvement_id: UUID):
        """
        Polls for incidents during the canary window. 
        If clean, promotes to 'applied'. If errors found, triggers 'rollback'.
        """
        patch = await self.db.get(SystemImprovement, improvement_id)
        if not patch or patch.status != "canary":
            return

        meta = (patch.test_results or {}).get("rollout_meta", {})
        until_str = meta.get("canary_until")
        if not until_str:
            return

        until_dt = datetime.fromisoformat(until_str)
        now = datetime.now(timezone.utc)

        # 1. Check if window is still open
        if now < until_dt:
            # Still observing
            return

        # 2. Check for related incidents (P0/P1 or related to file)
        start_dt = datetime.fromisoformat(meta.get("canary_start"))
        
        stmt = (
            select(OperationalIncident)
            .where(OperationalIncident.created_at >= start_dt)
            .where(OperationalIncident.status == "open")
            .where(
                (OperationalIncident.message.contains(patch.target_file)) | 
                (OperationalIncident.severity.in_(["critical", "high"]))
            )
        )
        
        result = await self.db.execute(stmt)
        blockers = result.scalars().all()

        if blockers:
            logger.warning(f"🚨 Blockers detected in canary window for {patch.target_file}. Triggering ROLLBACK.")
            await self.rollback(improvement_id, reason=f"Detected {len(blockers)} incidents during observation window.")
        else:
            logger.info(f"🏆 No incidents detected in 15m window. Promoting {improvement_id} to production.")
            patch.status = "applied"
            # Finalize metadata
            meta["status"] = "promoted"
            meta["promoted_at"] = now.isoformat()
            patch.test_results["rollout_meta"] = meta
            await self.db.commit()

    async def rollback(self, improvement_id: UUID, reason: str = "Manual/System rollback"):
        """
        Reverts the system using the recorded Snapshot Tag.
        """
        patch = await self.db.get(SystemImprovement, improvement_id)
        if not patch:
            return

        meta = (patch.test_results or {}).get("rollout_meta", {})
        snapshot_tag = meta.get("snapshot_tag")

        logger.error(f"🛑 EMERGENCY ROLLBACK: {patch.target_file} | Reason: {reason}")
        
        if snapshot_tag:
            try:
                self.rb_mgr.rollback_to_tag(snapshot_tag)
                logger.info(f"✅ System reverted to {snapshot_tag}")
            except Exception as e:
                logger.error(f"❌ Rollback execution failed: {e}")
        else:
            logger.warning("No snapshot tag found for rollback. Attempting manual file revert? (Not implemented)")

        # Update DB Status
        patch.status = "rolled_back"
        meta["status"] = "rolled_back"
        meta["rollback_reason"] = reason
        meta["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        patch.test_results["rollout_meta"] = meta
        
        await self.db.commit()
