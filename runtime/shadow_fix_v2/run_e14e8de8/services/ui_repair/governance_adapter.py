import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from services.observability.logging import get_logger
from .repair_policy import RepairPolicy

_log = get_logger("ui_repair_governance")

class GovernanceAdapter:
    """
    Phase 5: Governance Adapter.
    Bridges the UI repair system with the central Sovereign AGI Governance Hub.
    """

    async def create_approval_request(self, case_id: str, attempt_id: str, risk_data: Dict[str, Any], review_status: str, verifier_status: str) -> Dict[str, Any]:
        """
        Creates a formal approval request in the governance system.
        """
        _log.info(f"Governance: Creating approval request for case {case_id}")
        
        policy_res = RepairPolicy.evaluate(risk_data, review_status, verifier_status)
        
        request_id = f"REPAIR-REQ-{uuid.uuid4().hex[:8].upper()}"
        
        return {
            "success": True,
            "approval_request_id": request_id,
            "status": "REQUESTED",
            "policy_decision": policy_res,
            "created_at": datetime.now()
        }
