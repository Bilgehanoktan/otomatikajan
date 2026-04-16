import logging
from typing import Dict, Any

logger = logging.getLogger("repair.verification.economic")

class EconomicVerifier:
    """Verifies if the proposed repair fits within the remaining financial quota."""
    
    async def verify(self, candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Checks the ROI and budget impact of the candidate."""
        logger.info(f"Running Economic Pass [Region: {context.get('region', 'Global')}]")
        
        estimated_cost = candidate_payload.get("estimated_cost", 0)
        available_budget = context.get("available_budget", 1000.0)
        
        # 1. Direct Budget Check
        if estimated_cost > available_budget:
            logger.warning(f"Economic Check FAILED: Cost ${estimated_cost} exceeds available budget ${available_budget}")
            return False
            
        # 2. Strategic Threshold Check (Phase 28)
        # We don't want to spend more than 50% of remaining budget on a single repair unless it's critical
        critical_threshold = available_budget * 0.5
        is_critical = context.get("is_critical", False)
        
        if estimated_cost > critical_threshold and not is_critical:
            logger.warning(f"Economic Check FAILED: Non-critical repair cost ${estimated_cost} exceeds 50% quota limit (${critical_threshold})")
            return False
            
        logger.info(f"Economic Pass: SUCCESS. Cost ${estimated_cost} is validated against fiscal policies.")
        return True
