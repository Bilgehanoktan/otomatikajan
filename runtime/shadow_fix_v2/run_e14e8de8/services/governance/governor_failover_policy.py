from typing import Dict, Any, Optional
from libs.db.models.governance_models import GovernorDomain

class GovernorFailoverPolicy:
    """Domain governor arızalarında meta governor'ın nasıl davranacağını belirler."""
    
    @staticmethod
    def get_failover_decision(domain: GovernorDomain) -> Dict[str, Any]:
        """
        Domain cevap vermediğinde veya circuit breaker açıkken 
        üretilecek 'fail-safe' kararı döner.
        """
        base = {
            "domain": domain,
            "risk_score": 0,
            "recommended_decision": "NO_ACTION",
            "is_failover": True
        }
        
        if domain == GovernorDomain.POLICY:
            # Policy kritik: Down ise her şeyi durdur
            return {
                **base,
                "risk_score": 1000,
                "recommended_decision": "BLOCK_AND_ESCALATE",
                "reason": "Policy engine unavailable. Fail-safe triggered."
            }
        
        if domain == GovernorDomain.INCIDENT:
            # Incident kritik: Down ise insan bağlamı iste
            return {
                **base,
                "risk_score": 800,
                "recommended_decision": "REQUIRES_HUMAN_CONTEXT",
                "reason": "Incident guard unavailable. Safety first."
            }
            
        if domain == GovernorDomain.REPAIR:
            # Repair down ise replay/repair yapma
            return {
                **base,
                "recommended_decision": "NO_ACTION",
                "reason": "Repair systems offline."
            }
            
        if domain == GovernorDomain.APPROVAL:
            # Approval down ise otomatik onay yapma
            return {
                **base,
                "recommended_decision": "REQUIRES_PRIME_REVIEW",
                "reason": "Approval queue unavailable."
            }
            
        return base
