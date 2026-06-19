from libs.db.models.ui_repair_models import UIGuardrailTuningProposal

class DefenseTuningPolicy:
    """Phase 25: Enforces safety constraints on guardrail tuning."""
    
    def validate_improvement(self, proposal: UIGuardrailTuningProposal) -> bool:
        """Ensures the proposal does not weaken global security policy."""
        # Check if threshold is being lowered (which usually means weakening)
        # Note: This depends on the field logic, here we assume higher is more secure
        curr = proposal.current_config_json.get("threshold", 0.5)
        prop = proposal.proposed_config_json.get("threshold", 0.5)
        
        # In a real system, this would be much more sophisticated
        # (e.g. comparing against hardcoded 'floor' values)
        if prop < curr:
            return False
            
        return True

    def requires_canary(self, proposal: UIGuardrailTuningProposal) -> bool:
        """Determines if a proposal needs a canary run based on risk level."""
        return proposal.risk_level in ["CRITICAL", "HIGH"]
