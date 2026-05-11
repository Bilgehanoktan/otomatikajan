import uuid
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy import select, and_
from libs.db.session import get_db_ctx
from libs.db.models.core_models import ApprovalRequest
from libs.db.models.governance_models import GovernorDomain
from services.governance.base_governor import BaseDomainGovernor
from services.observability.logging import get_logger

from pydantic import BaseModel, Field

logger = get_logger("governance.approval_governor")

class GovernorCase(BaseModel):
    project_id: str
    title: str
    status: str
    source: str = "UNKNOWN"
    priority: str = "MEDIUM"
    recommended_action: str
    risk_score: float = 0.0
    risk_class: str = "LOW"
    pending_reason: Optional[str] = None
    rationale: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ApprovalGovernor(BaseDomainGovernor):
    """
    Onay kuyruğuna (Approval Queue) odaklanan Domain Governor.
    Auto-approve uygunluğunu ve bekleyen talepleri denetler.
    """

    def __init__(self):
        super().__init__(domain=GovernorDomain.APPROVAL)

    async def build_case(self, project_id: UUID) -> Dict[str, Any]:
        async with get_db_ctx() as session:
            res = await session.execute(
                select(ApprovalRequest)
                .where(and_(
                    ApprovalRequest.project_id == project_id,
                    ApprovalRequest.status == "pending"
                ))
            )
            approvals = res.scalars().all()
            
            approval_data = [
                {"id": str(a.id), "type": a.request_type, "reason": a.reason}
                for a in approvals
            ]

            return {
                "project_id": project_id,
                "pending_approvals": approval_data,
                "approval_count": len(approval_data)
            }

    async def score_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        if not case or not case.get("pending_approvals"):
            return {"risk_score": 0, "reason_codes": []}

        # Sadece onay bekliyor olması kendi başına yüksek risk değil
        score = 0.05 * len(case.get("pending_approvals", []))
        reasons = ["PENDING_APPROVAL_REQUESTS"]

        case["risk_score"] = self.normalize_risk_score(min(score, 0.3))
        case["reason_codes"] = self.normalize_reason_codes(reasons)
        return case

    async def decide(self, scored_case: Dict[str, Any]) -> Dict[str, Any]:
        if not scored_case or not scored_case.get("pending_approvals"):
            return {
                "domain": self.domain.value,
                "recommended_decision": "NO_ACTION",
                "risk_score": 0,
                "reason_codes": []
            }

        decision = {
            "domain": self.domain.value,
            "recommended_decision": "AUTO_APPROVE_CANDIDATE",
            "risk_score": scored_case["risk_score"],
            "reason_codes": scored_case["reason_codes"],
            "requires_prime": 0,
            "requires_quorum": 0
        }

        # Eğer çok fazla onay birikmişse (örn > 3), Prime baksa iyi olur
        if scored_case.get("approval_count", 0) > 3:
            self.mark_requires_prime(decision)
            decision["recommended_decision"] = "REQUIRES_PRIME_REVIEW"

        return decision

    async def execute(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {"executed": False, "msg": "Approval execution delegated to MetaGovernor"}

    async def emit_lineage(self, case: Dict[str, Any], decision: Dict[str, Any], outcome: Optional[Dict[str, Any]] = None):
        pass
