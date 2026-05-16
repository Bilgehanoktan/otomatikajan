import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIPolicyRegressionRun, UIGuardrailTuningProposal, GuardrailTuningStatus
)
from services.observability.logging import get_logger

_log = get_logger("regression_verifier")

class PolicyRegressionVerifier:
    """Phase 25: Replays historical events to verify policy changes against regressions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_regression(self, proposal_id: uuid.UUID) -> UIPolicyRegressionRun:
        """Executes a regression test for a given proposal."""
        proposal_stmt = select(UIGuardrailTuningProposal).where(UIGuardrailTuningProposal.id == proposal_id)
        proposal_res = await self.db.execute(proposal_stmt)
        proposal = proposal_res.scalar_one_or_none()
        
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found.")
            
        _log.info(f"Starting regression run for proposal {proposal.proposal_key}...")
        
        run = UIPolicyRegressionRun(
            id=uuid.uuid4(),
            proposal_id=proposal_id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        await self.db.flush()
        
        # 1. Fetch historical events (Mocked for Phase 25)
        # In production, we'd query DecisionLineage or EvidenceLedger
        history = self._get_mock_event_history()
        
        allowed = 0
        denied = 0
        false_blocks = 0
        false_allows = 0
        
        new_config = proposal.proposed_config_json
        threshold = new_config.get("threshold", 0.5)
        
        for event in history:
            # 2. Re-evaluate event with NEW policy
            actual_risk = event["risk"]
            should_allow = actual_risk < threshold
            
            if should_allow:
                allowed += 1
                if not event["is_legitimate"]:
                    false_allows += 1 # Regression: We allowed something bad
            else:
                denied += 1
                if event["is_legitimate"]:
                    false_blocks += 1 # Regression: We blocked something good
                    
        # 3. Calculate regression score
        total = len(history)
        # Score decreases with false blocks and false allows
        score = max(0, 1.0 - (false_blocks * 0.1) - (false_allows * 0.05))
        
        run.status = "PASSED" if score > 0.8 else "FAILED"
        run.tested_events_count = total
        run.allowed_count = allowed
        run.denied_count = denied
        run.false_allow_count = false_allows
        run.false_block_count = false_blocks
        run.regression_score = score
        run.finished_at = datetime.now(timezone.utc)
        run.result_summary_json = {
            "analysis": f"Regression score: {score:.2f}",
            "recommendation": "PROCEED" if run.status == "PASSED" else "ADJUST_THRESHOLD"
        }
        
        # 4. Update Proposal Status
        proposal.status = GuardrailTuningStatus.REGRESSION_PASSED if run.status == "PASSED" else GuardrailTuningStatus.REGRESSION_FAILED
        
        await self.db.commit()
        _log.info(f"Regression run completed. Status: {run.status}, Score: {score:.2f}")
        
        return run

    def _get_mock_event_history(self) -> List[Dict[str, Any]]:
        """Mocked history of policy evaluations."""
        return [
            {"id": "EV-001", "risk": 0.2, "is_legitimate": True},
            {"id": "EV-002", "risk": 0.3, "is_legitimate": True},
            {"id": "EV-003", "risk": 0.9, "is_legitimate": False},
            {"id": "EV-004", "risk": 0.6, "is_legitimate": True},
            {"id": "EV-005", "risk": 0.1, "is_legitimate": True},
            {"id": "EV-006", "risk": 0.95, "is_legitimate": False},
            {"id": "EV-007", "risk": 0.75, "is_legitimate": False},
            {"id": "EV-008", "risk": 0.4, "is_legitimate": True},
            {"id": "EV-009", "risk": 0.55, "is_legitimate": True},
            {"id": "EV-010", "risk": 0.85, "is_legitimate": False},
        ]
