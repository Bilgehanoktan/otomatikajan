"""
Approval Governor Calibration Service (Faz 6)
Analyzes outcome performance and generates calibration proposals.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.repositories.governor_outcome_repository import GovernorOutcomeRepo
from libs.db.repositories.governor_calibration_repository import GovernorCalibrationRepo
from services.governance.approval_governor_config import ApprovalGovernorConfig
from services.observability.logging import get_logger

logger = get_logger("governance.calibration")

class ApprovalGovernorCalibration:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.outcome_repo = GovernorOutcomeRepo()
        self.calibration_repo = GovernorCalibrationRepo()
        self.config = ApprovalGovernorConfig()

    async def generate_calibration_proposals(self, window_days: int = 14) -> List[uuid.UUID]:
        """
        Tüm parametreleri değerlendirir ve gerekli ise yeni öneriler oluşturur.
        """
        proposals = []
        
        # 1. Evaluate Auto Approve
        proposal_id = await self.evaluate_auto_approve_threshold(window_days)
        if proposal_id: proposals.append(proposal_id)
        
        # 2. Evaluate Auto Replay
        proposal_id = await self.evaluate_auto_replay_threshold(window_days)
        if proposal_id: proposals.append(proposal_id)
        
        # 3. Evaluate Prime Escalation
        proposal_id = await self.evaluate_prime_escalation_threshold(window_days)
        if proposal_id: proposals.append(proposal_id)
        
        return proposals

    async def evaluate_auto_approve_threshold(self, window_days: int) -> Optional[uuid.UUID]:
        parameter = "AUTO_APPROVE_MAX_RISK"
        metrics = await self.outcome_repo.aggregate_metrics(self.db, window_days=window_days)
        accuracy = metrics.get("accuracy", 0)
        total = metrics.get("total_decisions", 0)
        
        if total < 20: # Sample size check
            return None
            
        current_val = await self.config.get_auto_approve_max_risk(self.db)
        bounds = self.config.get_bounds()[parameter]
        
        new_val = current_val
        reason = ""
        
        if accuracy < 85: # Too many errors, decrease autonomy
            new_val = max(bounds[0], current_val - 0.05)
            reason = f"Karar doğruluğu ({accuracy:.1f}%) düşük. Otonomi daraltılıyor."
        elif accuracy > 96 and current_val < bounds[1]: # High accuracy, maybe increase autonomy
            new_val = min(bounds[1], current_val + 0.02)
            reason = f"Karar doğruluğu ({accuracy:.1f}%) yüksek. Otonomi genişletilebilir."
            
        if new_val != current_val:
            proposal = await self.calibration_repo.create_proposal(self.db, {
                "parameter_name": parameter,
                "old_value": current_val,
                "proposed_value": new_val,
                "change_reason": reason,
                "confidence_score": 0.8,
                "window_days": window_days,
                "sample_size": total
            })
            return proposal.id
            
        return None

    async def evaluate_auto_replay_threshold(self, window_days: int) -> Optional[uuid.UUID]:
        parameter = "AUTO_REPLAY_MAX_RISK"
        metrics = await self.outcome_repo.aggregate_metrics(self.db, window_days=window_days)
        replay_success = metrics.get("replay_success_rate", 0)
        total = metrics.get("total_decisions", 0) # This should be replay count actually
        
        # Replay specific metrics would be better, but using aggregate_metrics for now
        if total < 10: 
            return None
            
        current_val = await self.config.get_auto_replay_max_risk(self.db)
        bounds = self.config.get_bounds()[parameter]
        
        new_val = current_val
        reason = ""
        
        if replay_success < 40: # Replays mostly failing
            new_val = max(bounds[0], current_val - 0.05)
            reason = f"Replay başarı oranı ({replay_success:.1f}%) düşük. Risk eşiği düşürülüyor."
        elif replay_success > 75 and current_val < bounds[1]:
            new_val = min(bounds[1], current_val + 0.05)
            reason = f"Replay başarısı ({replay_success:.1f}%) tatminkar. Daha cesur replay denenebilir."

        if new_val != current_val:
            proposal = await self.calibration_repo.create_proposal(self.db, {
                "parameter_name": parameter,
                "old_value": current_val,
                "proposed_value": new_val,
                "change_reason": reason,
                "confidence_score": 0.7,
                "window_days": window_days,
                "sample_size": total
            })
            return proposal.id
        return None

    async def evaluate_prime_escalation_threshold(self, window_days: int) -> Optional[uuid.UUID]:
        # Implementation of Prime escalation logic
        # If Operator overrode too many auto-approves, decrease prime escalation min risk
        # (Meaning: Escalate more items to Prime)
        parameter = "PRIME_ESCALATION_MIN_RISK"
        metrics = await self.outcome_repo.aggregate_metrics(self.db, window_days=window_days)
        # We need "Prime Agreement" metric here.
        # For now, placeholder based on accuracy
        accuracy = metrics.get("accuracy", 0)
        if accuracy < 90:
            current_val = await self.config.get_prime_escalation_min_risk(self.db)
            bounds = self.config.get_bounds()[parameter]
            new_val = max(bounds[0], current_val - 0.10)
            
            proposal = await self.calibration_repo.create_proposal(self.db, {
                "parameter_name": parameter,
                "old_value": current_val,
                "proposed_value": new_val,
                "change_reason": f"Genel doğruluk ({accuracy:.1f}%) düştüğü için Prime denetimi sıkılaştırılıyor.",
                "confidence_score": 0.9,
                "window_days": window_days,
                "sample_size": metrics.get("total_decisions", 0)
            })
            return proposal.id
        return None
