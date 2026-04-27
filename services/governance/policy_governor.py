import uuid
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy import select, and_
from libs.db.session import get_db_ctx
from libs.db.models.governance_models import GovernorDomain, PolicyProposal
from services.governance.base_governor import BaseDomainGovernor
from services.observability.logging import get_logger

logger = get_logger("governance.policy_governor")

class PolicyGovernor(BaseDomainGovernor):
    """
    Politika ve anayasal uyuma odaklanan Domain Governor.
    Policy proposal, quorum zorunluluğu ve korumalı modül erişimlerini denetler.
    """

    def __init__(self):
        super().__init__(domain=GovernorDomain.POLICY)

    async def build_case(self, project_id: UUID) -> Dict[str, Any]:
        async with get_db_ctx() as session:
            # Bu örnekte projenin bir politika değişikliği tetikleyip tetiklemediğine bakıyoruz.
            # Gerçek senaryoda projenin amacını (goal) analiz ederek 'CONSTITUTIONAL_EFFECT' tespiti yapar.
            res = await session.execute(
                select(PolicyProposal)
                .where(and_(
                    PolicyProposal.status == "PROPOSED",
                    # PolicyProposal'da project_id olmayabilir, genelde GLOBAL'dir.
                    # Ama proje bazlı politika teklifleri için varsayıyoruz.
                ))
                .limit(1)
            )
            proposal = res.scalar_one_or_none()

            return {
                "project_id": project_id,
                "has_policy_proposal": proposal is not None,
                "proposal_scope": proposal.scope if proposal else None,
                "is_protected_module": False # Placeholder logic
            }

    async def score_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        score = 0.0
        reasons = []

        if case.get("has_policy_proposal"):
            score += 0.5
            reasons.append("POLICY_CHANGE_DETECTED")
            if case.get("proposal_scope") == "GLOBAL":
                score += 0.3
                reasons.append("GLOBAL_SCOPE_IMPACT")

        if case.get("is_protected_module"):
            score += 0.7
            reasons.append("PROTECTED_MODULE_ACCESS")

        case["risk_score"] = self.normalize_risk_score(score)
        case["reason_codes"] = self.normalize_reason_codes(reasons)
        return case

    async def decide(self, scored_case: Dict[str, Any]) -> Dict[str, Any]:
        decision = {
            "domain": self.domain.value,
            "recommended_decision": "NO_ACTION",
            "risk_score": scored_case.get("risk_score", 0),
            "reason_codes": scored_case.get("reason_codes", []),
            "requires_prime": 0,
            "requires_quorum": 0
        }

        risk = scored_case.get("risk_score", 0)
        if risk >= 700:
            self.mark_requires_quorum(decision)
            decision["recommended_decision"] = "REQUIRES_QUORUM"
        elif risk >= 400:
            self.mark_requires_prime(decision)
            decision["recommended_decision"] = "REQUIRES_PRIME_REVIEW"

        return decision

    async def execute(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {"executed": False, "msg": "Policy enforcement delegated to MetaGovernor"}

    async def emit_lineage(self, case: Dict[str, Any], decision: Dict[str, Any], outcome: Optional[Dict[str, Any]] = None):
        pass
