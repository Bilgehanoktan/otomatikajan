"""
Sovereign AGI — Phase 29
services/validation/continuous_validation_service.py
Background service for running health probes and verifying system integrity.
"""

import asyncio
from typing import List, Dict, Any, Optional
from services.governance.signoff_registry import SignoffRegistry
from libs.db.models.governance_models import ValidationType, ValidationStatus
from services.observability.logging import get_logger

logger = get_logger("validation.continuous")

class ContinuousValidationService:
    def __init__(self):
        self.is_running = False
        self._lock = asyncio.Lock()

    async def start(self):
        """Doğrulama döngüsünü başlatır."""
        async with self._lock:
            if self.is_running:
                return
            self.is_running = True
        
        logger.info("Continuous Validation Service STARTED.")
        asyncio.create_task(self._loop())

    async def stop(self):
        """Doğrulama döngüsünü durdurur."""
        async with self._lock:
            self.is_running = False
        logger.info("Continuous Validation Service STOPPED.")

    async def _loop(self):
        """Periyodik doğrulama döngüsü (Örn: Her 15 dakikada bir)."""
        while self.is_running:
            try:
                await self.run_probe_cycle()
            except Exception as e:
                logger.error(f"Error in validation loop: {e}")
            
            await asyncio.sleep(900) # 15 dakika

    async def run_probe_cycle(self):
        """
        Sistemin tüm bileşenleri için sağlık taraması yapar.
        Stage 2: ProofEngine tetiklenir.
        """
        from services.validation.proof_engine import proof_engine
        
        components = ["RepairOrchestrator", "WorkflowAPI", "BudgetGuard", "AuthService"]
        
        for comp in components:
            logger.debug(f"Probing {comp}...")
            # ProofEngine üzerinden gerçek/mock testi koştur
            await proof_engine.run_suite(
                component_name=comp,
                suite_name="BasicHealth",
                v_type=ValidationType.CONTINUOUS
            )

    async def trigger_manual_validation(self, component_name: str) -> bool:
        """Kullanıcı isteğiyle anlık doğrulama tetikler."""
        logger.info(f"Manual validation triggered for {component_name}")
        from services.validation.proof_engine import proof_engine
        
        await proof_engine.run_suite(
            component_name=component_name,
            suite_name="BasicHealth", # Veya manual suite
            v_type=ValidationType.MANUAL
        )
        return True
