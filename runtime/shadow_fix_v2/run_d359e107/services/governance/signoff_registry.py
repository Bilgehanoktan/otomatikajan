"""
Sovereign AGI — Phase 29
services/governance/signoff_registry.py
Registry service for managing component sign-offs and production readiness state.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import ProductionSignoff, SignoffStatus, ValidationResult, ValidationStatus
from libs.db.session import AsyncSessionLocal
from services.observability.logging import get_logger

logger = get_logger("governance.signoff")

class SignoffRegistry:
    @staticmethod
    async def get_latest_signoff(component_name: str) -> Optional[ProductionSignoff]:
        """Bileşen için en güncel onay kaydını döner."""
        async with AsyncSessionLocal() as session:
            stmt = (
                select(ProductionSignoff)
                .where(ProductionSignoff.component_name == component_name)
                .order_by(desc(ProductionSignoff.created_at))
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def create_signoff(
        component_name: str,
        version: str,
        status: SignoffStatus = SignoffStatus.SIGNED,
        approver_id: Optional[str] = None,
        approver_note: Optional[str] = None,
        evidence_summary: Optional[Dict[str, Any]] = None
    ) -> ProductionSignoff:
        """Yeni bir üretim onay kaydı oluşturur."""
        async with AsyncSessionLocal() as session:
            new_signoff = ProductionSignoff(
                component_name=component_name,
                version=version,
                status=status,
                approver_id=approver_id,
                approver_note=approver_note,
                evidence_summary=evidence_summary
            )
            session.add(new_signoff)
            await session.commit()
            await session.refresh(new_signoff)
            logger.info(f"New sign-off created for {component_name} v{version}: {status}")
            return new_signoff

    @staticmethod
    async def revoke_signoff(signoff_id: str, reason: str):
        """Mevcut bir onayı iptal eder (REVOKED)."""
        async with AsyncSessionLocal() as session:
            stmt = select(ProductionSignoff).where(ProductionSignoff.id == signoff_id)
            result = await session.execute(stmt)
            signoff = result.scalar_one_or_none()
            if signoff:
                signoff.status = SignoffStatus.REVOKED
                signoff.approver_note = (signoff.approver_note or "") + f"\n[REVOKE REASON]: {reason}"
                await session.commit()
                logger.warning(f"Sign-off {signoff_id} REVOKED. Reason: {reason}")
                return True
            return False

    @staticmethod
    async def record_validation_result(
        component_name: str,
        test_suite: str,
        v_type: Any, # ValidationType enum
        status: ValidationStatus,
        metrics: Optional[Dict[str, Any]] = None,
        logs: Optional[str] = None,
        signoff_id: Optional[str] = None
    ) -> ValidationResult:
        """Bir doğrulama testi sonucunu kaydeder."""
        async with AsyncSessionLocal() as session:
            result = ValidationResult(
                component_name=component_name,
                test_suite=test_suite,
                validation_type=v_type,
                status=status,
                metrics=metrics,
                raw_logs=logs,
                signoff_id=signoff_id
            )
            session.add(result)
            await session.commit()
            await session.refresh(result)
            logger.info(f"Validation result recorded for {component_name} [{test_suite}]: {status}")
            return result

    @staticmethod
    async def is_ready_for_production(component_name: str) -> bool:
        """
        Bileşenin üretim için hazır olup olmadığını kontrol eder.
        Kriterler:
        1. En güncel kaydı SIGNED olmalı.
        2. Son 24 saatte başarısız CONTINUOUS doğrulama olmamalı (opsiyonel sıkı kural).
        """
        signoff = await SignoffRegistry.get_latest_signoff(component_name)
        if not signoff or signoff.status != SignoffStatus.SIGNED:
            return False
            
        # Buraya ek kural olarak son validation sonuçları eklenebilir.
        return True
