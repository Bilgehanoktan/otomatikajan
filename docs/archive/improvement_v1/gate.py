from .models import VerificationResult, GateDecision

class ImprovementGate:
    """Decides whether a verified patch should be presented to a human or rejected."""

    async def evaluate(self, result: VerificationResult) -> GateDecision:
        """
        Decision logic:
        - If tests failed -> REJECT
        - If security check failed -> ABORT
        - If benchmark regressed significantly -> REJECT
        - Otherwise -> APPROVE (present to human)
        """
        if not result.tests_passed:
            return GateDecision(
                proposal_id=result.proposal_id,
                decision="reject",
                reason="Regression detected: tests failed."
            )
        
        if not result.security_ok:
            return GateDecision(
                proposal_id=result.proposal_id,
                decision="abort",
                reason="Security violation detected in patch."
            )
            
        return GateDecision(
            proposal_id=result.proposal_id,
            decision="approve",
            reason="Tests passed and performance improved. Ready for human review."
        )
