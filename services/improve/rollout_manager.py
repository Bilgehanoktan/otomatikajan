from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime, timezone, timedelta
import logging
from uuid import UUID
from pathlib import Path
from sqlalchemy import select, and_
from libs.db.models.core_models import SystemImprovement, OperationalIncident, Project, SovereignEvidence
from services.orchestration.application.self_updater import SelfUpdater
from services.orchestration.application.rollback_manager import RollbackManager
from services.orchestration.calibration_engine import calibration_engine

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

    async def log_evidence(self, evidence_type: str, severity: str, 
                         project_id: Optional[UUID] = None, 
                         incident_id: Optional[UUID] = None,
                         improvement_id: Optional[UUID] = None,
                         payload: Dict[str, Any] = None):
        """Phase 26: R-01 Live Field Evidence Logger"""
        try:
            evidence = SovereignEvidence(
                evidence_type=evidence_type,
                severity=severity,
                project_id=project_id,
                incident_id=incident_id,
                improvement_id=improvement_id,
                payload=payload or {},
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(evidence)
            await self.db.flush()
            logger.debug(f"📊 Evidence Logged: {evidence_type} (ImpID: {improvement_id})")
        except Exception as e:
            logger.error(f"Failed to log evidence in RolloutManager: {e}")

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

            # R-05 Calibration Loop: Record Canary Success (Promotion)
            calibration_engine.record_correction(
                incident_id="canary_promotion",
                action="canary_success",
                risk_score=patch.risk_score,
                is_success=True
            )
            
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

        # R-05 Calibration Loop: Record Canary Fail and Rollback
        calibration_engine.record_correction(
            incident_id=str(patch.id),
            action="canary_fail",
            risk_score=patch.risk_score,
            is_success=False
        )
        calibration_engine.record_correction(
            incident_id=str(patch.id),
            action="rollback",
            risk_score=patch.risk_score,
            is_success=True
        )
        
        await self.db.commit()
