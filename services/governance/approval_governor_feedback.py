"""
Approval Governor Feedback Service (Faz 5)
Evaluates governor decisions against final outcomes to compute quality and accuracy.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import (
    GovernorCaseRecord, GovernorActionRecord, GovernorOutcomeRecord,
    GovernorOutcomeType, GovernorDecisionQuality
)
from libs.db.repositories.governor_outcome_repository import GovernorOutcomeRepo
from services.observability.logging import get_logger

logger = get_logger("governance.feedback")

class ApprovalGovernorFeedbackService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GovernorOutcomeRepo()

    async def record_execution_outcome(self, 
                                     case: GovernorCaseRecord, 
                                     action: GovernorActionRecord, 
                                     project_state: str) -> Optional[GovernorOutcomeRecord]:
        """
        Bir governor aksiyonu sonrası (genelde workflow terminal olduğunda) sonucu kaydeder.
        """
        logger.info(f"Recording outcome for case {case.id}, action {action.action_type}, project_state {project_state}")
        
        outcome_type = GovernorOutcomeType.NO_SIGNAL
        quality = GovernorDecisionQuality.PARTIAL
        was_successful = 0
        
        # Karar/Sonuç Eşleştirme Mantığı
        if action.action_type == "AUTO_APPROVE":
            if project_state == "COMPLETED":
                outcome_type = GovernorOutcomeType.SUCCESS
                quality = GovernorDecisionQuality.CORRECT
                was_successful = 1
            elif project_state == "FAILED":
                outcome_type = GovernorOutcomeType.FAILED
                quality = GovernorDecisionQuality.FALSE_POSITIVE
                
        elif action.action_type == "AUTO_REPLAY":
            if project_state == "COMPLETED":
                outcome_type = GovernorOutcomeType.SUCCESS
                quality = GovernorDecisionQuality.CORRECT
                was_successful = 1
            elif project_state == "FAILED":
                outcome_type = GovernorOutcomeType.FAILED
                quality = GovernorDecisionQuality.FALSE_POSITIVE
        
        elif action.action_type == "ARCHIVE_STALE":
            # Arşivleme sonrası restore edilmediyse SUCCESS kabul edebiliriz (şimdilik)
            outcome_type = GovernorOutcomeType.SUCCESS
            quality = GovernorDecisionQuality.CORRECT
            was_successful = 1

        # Gecikme hesapla
        latency = (datetime.now(timezone.utc) - case.created_at).total_seconds()

        outcome_data = {
            "case_id": case.id,
            "project_id": case.project_id,
            "action_id": action.id,
            "decision": case.recommended_decision,
            "final_outcome": outcome_type,
            "quality": quality,
            "was_successful": was_successful,
            "resolution_latency_seconds": int(latency),
            "reason_codes": case.decision_reason_codes,
            "snapshot_payload": case.snapshot_payload
        }
        
        return await self.repo.create_outcome(self.db, outcome_data)

    async def record_override_outcome(self, 
                                    case: GovernorCaseRecord, 
                                    override_action: str) -> Optional[GovernorOutcomeRecord]:
        """
        Operatör governor kararını ezdiğinde sonucu kaydeder.
        """
        logger.info(f"Recording override outcome for case {case.id}, override: {override_action}")
        
        quality = GovernorDecisionQuality.FALSE_POSITIVE
        
        # Eğer governor eskalasyon istediyse ve operatör aksiyon aldıysa bu CORRECT'tir.
        if case.recommended_decision in ("REQUIRES_PRIME_REVIEW", "REQUIRES_QUORUM"):
            quality = GovernorDecisionQuality.CORRECT
            
        outcome_data = {
            "case_id": case.id,
            "project_id": case.project_id,
            "decision": case.recommended_decision,
            "final_outcome": GovernorOutcomeType.REVERSED,
            "quality": quality,
            "operator_overrode": 1,
            "resolution_latency_seconds": int((datetime.now(timezone.utc) - case.created_at).total_seconds()),
            "reason_codes": case.decision_reason_codes
        }
        
        return await self.repo.create_outcome(self.db, outcome_data)
