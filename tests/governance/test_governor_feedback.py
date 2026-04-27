import pytest
import uuid
from datetime import datetime, timezone
from services.governance.approval_governor_feedback import ApprovalGovernorFeedbackService
from libs.db.models.governance_models import (
    GovernorCaseRecord, GovernorActionRecord, GovernorOutcomeType, GovernorDecisionQuality
)
from libs.db.session import get_db_ctx

@pytest.mark.asyncio
async def test_record_execution_outcome_success():
    async with get_db_ctx() as db:
        feedback_svc = ApprovalGovernorFeedbackService(db)
        
        case = GovernorCaseRecord(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            recommended_decision="AUTO_APPROVE_CANDIDATE",
            pending_reason="PENDING_APPROVAL",
            risk_class="LOW",
            risk_score=100
        )
        db.add(case)
        await db.flush()
        
        action = GovernorActionRecord(
            id=uuid.uuid4(),
            project_id=case.project_id,
            case_id=case.id,
            action_type="AUTO_APPROVE",
            status="executed"
        )
        db.add(action)
        await db.flush()
        
        outcome = await feedback_svc.record_execution_outcome(case, action, "COMPLETED")
        
        assert outcome is not None
        assert outcome.final_outcome == GovernorOutcomeType.SUCCESS
        assert outcome.quality == GovernorDecisionQuality.CORRECT
        assert outcome.was_successful == 1
        await db.rollback()

@pytest.mark.asyncio
async def test_record_override_outcome():
    async with get_db_ctx() as db:
        feedback_svc = ApprovalGovernorFeedbackService(db)
        
        case = GovernorCaseRecord(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            recommended_decision="AUTO_APPROVE_CANDIDATE",
            pending_reason="PENDING_APPROVAL",
            risk_class="LOW",
            risk_score=100,
            created_at=datetime.now(timezone.utc)
        )
        db.add(case)
        await db.flush()
        
        outcome = await feedback_svc.record_override_outcome(case, "REJECT")
        
        assert outcome.final_outcome == GovernorOutcomeType.REVERSED
        assert outcome.quality == GovernorDecisionQuality.FALSE_POSITIVE
        await db.rollback()
