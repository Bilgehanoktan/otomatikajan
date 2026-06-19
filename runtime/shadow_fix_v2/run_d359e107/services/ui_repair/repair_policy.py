from typing import Dict, Any

class RepairPolicy:
    """
    Phase 5: Policy engine for autonomous repairs.
    Determines if a repair requires manual approval based on risk and verification status.
    """

    @staticmethod
    def evaluate(risk_data: Dict[str, Any], review_status: str, verifier_status: str) -> Dict[str, Any]:
        """
        Evaluates the repair against governance policies.
        """
        risk_level = risk_data.get("risk_level", "LOW")
        
        requires_operator = True
        auto_apply = False
        
        # Policy: Only LOW risk changes with PASSED review and PASSED verification can be auto-applied
        # In this Phase, we default to requires_operator=True for safety as requested.
        if risk_level == "LOW" and review_status == "PASSED" and verifier_status == "PASSED":
            # For Phase 5 demonstration, we still keep operator approval as True but note that auto is *possible*
            auto_apply = False 
            decision = "Policy permits auto-approval, but human-in-the-loop is enforced for Phase 5."
        elif risk_level == "HIGH":
            requires_operator = True
            decision = "HIGH RISK: Manual operator review is strictly required."
        else:
            requires_operator = True
            decision = "Standard policy: Operator approval required for verification."

        return {
            "risk_level": risk_level,
            "requires_operator_approval": requires_operator,
            "auto_apply_allowed": auto_apply,
            "policy_decision": decision,
            "requires_pr_agent_review": True,
            "requires_verifier_mesh": True
        }
