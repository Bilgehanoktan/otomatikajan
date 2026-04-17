"""
Sovereign AGI — Phase 29
services/training/drill_engine.py
The engine for running governance drills and synthetic simulations.
Verifies system readiness without impacting production services.
"""

import asyncio
import uuid
from typing import List, Dict, Any
from services.repair.repair_orchestrator import RepairOrchestrator
from services.repair.schemas.incident import IncidentRecord
from services.observability.logging import get_logger
from services.governance.signoff_registry import SignoffRegistry
from libs.db.models.governance_models import ValidationType, ValidationStatus

logger = get_logger("training.drill")

class DrillEngine:
    def __init__(self, orchestrator: RepairOrchestrator):
        self.orchestrator = orchestrator
        self.is_running = False
        self._loop_task = None

    async def start_automated_drills(self, frequency_hours: int = 24):
        """Otomatik tatbikat döngüsünü başlatır."""
        if self.is_running:
            return
        self.is_running = True
        self._loop_task = asyncio.create_task(self._automated_drill_loop(frequency_hours))
        logger.info(f"Automated drill engine started (Frequency: every {frequency_hours} hours)")

    async def stop_automated_drills(self):
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
        logger.info("Automated drill engine stopped.")

    async def _automated_drill_loop(self, frequency_hours: int):
        while self.is_running:
            try:
                scenarios = await self.list_available_scenarios()
                if scenarios:
                    import random
                    scenario = random.choice(scenarios)
                    logger.info(f"[AUTOMATED-DRILL] Starting scheduled drill: {scenario}")
                    await self.run_governance_drill(scenario)
                
                await asyncio.sleep(frequency_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[AUTOMATED-DRILL] Loop error: {e}")
                await asyncio.sleep(300)

    async def run_governance_drill(self, scenario_name: str) -> Dict[str, Any]:
        """Bir yönetişim tatbikatı başlatır."""
        logger.info(f"Initiating Governance Drill: {scenario_name}")
        
        # 1. Sentetik bir incident oluştur
        incident = IncidentRecord(
            incident_id=f"drill_{uuid.uuid4().hex[:8]}",
            symptom=f"DRILL SCENARIO: {scenario_name}",
            module="DrillSystem",
            severity="info",
            context={"mode": "drill", "scenario": scenario_name}
        )
        
        # 2. RepairOrchestrator'ı SHADOW modda tetikle
        result = await self.orchestrator.shadow_repair_cycle(
            incident_type="DRILL_GOVERNANCE",
            payload={"scenario": scenario_name, "incident": incident.dict()}
        )
        
        # 3. Sonucu Registry'e "DRILL" olarak kaydet
        status = ValidationStatus.PASS if result.get("status") == "REPAIR_SUCCESS" else ValidationStatus.FAIL
        
        await SignoffRegistry.record_validation_result(
            component_name="SovereignAGI_Core",
            test_suite=f"Drill_{scenario_name}",
            v_type=ValidationType.DRILL,
            status=status,
            metrics={
                "winning_score": result.get("winning_score", 0.0),
                "candidates": result.get("candidates_count", 0)
            },
            logs=result.get("summary", "Drill complete")
        )
        
        return {
            "scenario": scenario_name,
            "status": status,
            "details": result
        }

    async def list_available_scenarios(self) -> List[str]:
        return [
            "RegionalFailoverDrill",
            "BudgetExhaustionBufferDrill",
            "PolicyCollisionArbitration",
            "SelfTuningCalibrationDrill"
        ]

# Global instance (Injected orchestrator will be set during app init)
drill_engine: Optional[DrillEngine] = None
