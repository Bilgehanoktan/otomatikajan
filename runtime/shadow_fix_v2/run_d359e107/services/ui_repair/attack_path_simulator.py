import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UIAttackPath, UIAttackSimulationRun, AttackPathType
)

logger = logging.getLogger(__name__)

class AttackPathSimulator:
    """Phase 23: Controlled, non-destructive simulation of adversarial attack paths."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_simulation(self, path_id: uuid.UUID, mode: str = "DRY_RUN") -> UIAttackSimulationRun:
        """
        Simulates an attack path to test the effectiveness of current guardrails.
        """
        stmt = select(UIAttackPath).where(UIAttackPath.id == path_id)
        result = await self.session.execute(stmt)
        path = result.scalar_one_or_none()
        
        if not path:
            raise ValueError(f"Attack path not found: {path_id}")
            
        logger.info(f"Starting simulation for path: {path.path_name} (Mode: {mode})")
        
        run = UIAttackSimulationRun(
            attack_path_id=path.id,
            status="RUNNING",
            simulation_mode=mode,
            started_at=datetime.now(timezone.utc)
        )
        self.session.add(run)
        await self.session.flush()
        
        # Simulate logic based on path type
        simulation_result = await self._execute_simulation_logic(path)
        
        run.status = "COMPLETED"
        run.finished_at = datetime.now(timezone.utc)
        run.detected_controls_json = simulation_result["detected_controls"]
        run.bypassed_controls_json = simulation_result["bypassed_controls"]
        run.blocked_by_json = simulation_result.get("blocked_by")
        run.result_summary_json = simulation_result["summary"]
        run.evidence_hash = f"SIM_{uuid.uuid4().hex[:16]}"
        
        await self.session.commit()
        return run

    async def _execute_simulation_logic(self, path: UIAttackPath) -> Dict[str, Any]:
        """
        Mock simulation logic testing guardrail triggers.
        """
        detected_controls = ["AuthZGate", "TenantBoundaryValidator", "PolicyEnforcer"]
        bypassed_controls = []
        blocked_by = None
        
        # Scenario-specific outcomes
        if path.path_type == AttackPathType.TENANT_ISOLATION_BYPASS.value:
            # Most critical, usually blocked early
            blocked_by = {"control": "TenantBoundaryValidator", "reason": "Target tenant mismatch in mesh routing table"}
            summary = {"outcome": "BLOCKED", "step_reached": 1}
        elif path.path_type == AttackPathType.IDENTITY_IMPERSONATION.value:
            # Might reach a bit further
            bypassed_controls = ["AuthZGate"]
            blocked_by = {"control": "PolicyEnforcer", "reason": "Revoked identity detection during tool call"}
            summary = {"outcome": "BLOCKED", "step_reached": 2}
        else:
            blocked_by = {"control": "SystemDefaultGuardrail", "reason": "Anomaly detected in operation pattern"}
            summary = {"outcome": "BLOCKED", "step_reached": 1}
            
        return {
            "detected_controls": detected_controls,
            "bypassed_controls": bypassed_controls,
            "blocked_by": blocked_by,
            "summary": summary
        }
