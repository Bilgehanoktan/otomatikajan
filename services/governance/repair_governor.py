import uuid
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy import select, and_
from libs.db.session import get_db_ctx
from libs.db.models.repair_models import RepairIncident, RepairJob
from libs.db.models.governance_models import GovernorDomain
from services.governance.base_governor import BaseDomainGovernor
from services.observability.logging import get_logger

logger = get_logger("governance.repair_governor")

class RepairGovernor(BaseDomainGovernor):
    """
    Otomatik onarım (Repair) süreçlerine odaklanan Domain Governor.
    Repair jobs, patch safety ve repair confidence denetler.
    """

    def __init__(self):
        super().__init__(domain=GovernorDomain.REPAIR)

    async def build_case(self, project_id: UUID) -> Dict[str, Any]:
        async with get_db_ctx() as session:
            # Proje ile ilişkili aktif repair işlerine bak
            res = await session.execute(
                select(RepairJob)
                .where(and_(
                    RepairJob.project_id == project_id,
                    RepairJob.status.in_(["pending", "running", "validating"])
                ))
            )
            jobs = res.scalars().all()
            
            job_data = []
            max_confidence = 0.0
            for job in jobs:
                conf = job.confidence or 0.0
                if conf > max_confidence:
                    max_confidence = conf
                
                job_data.append({
                    "id": str(inc.id) if hasattr(job, "id") else None,
                    "status": job.status,
                    "confidence": conf
                })

            return {
                "project_id": project_id,
                "has_active_repair": len(job_data) > 0,
                "repair_jobs": job_data,
                "max_repair_confidence": max_confidence
            }

    async def score_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        if not case or not case.get("has_active_repair"):
            return {"risk_score": 0, "reason_codes": []}

        score = 0.0
        reasons = []
        
        conf = case.get("max_repair_confidence", 0.0)
        if conf < 0.4:
            score += 0.5
            reasons.append("LOW_REPAIR_CONFIDENCE")
        elif conf < 0.7:
            score += 0.2
            reasons.append("MEDIUM_REPAIR_CONFIDENCE")
        else:
            reasons.append("HIGH_REPAIR_CONFIDENCE")

        case["risk_score"] = self.normalize_risk_score(score)
        case["reason_codes"] = self.normalize_reason_codes(reasons)
        return case

    async def decide(self, scored_case: Dict[str, Any]) -> Dict[str, Any]:
        if not scored_case or not scored_case.get("has_active_repair"):
            return {
                "domain": self.domain.value,
                "recommended_decision": "NO_ACTION",
                "risk_score": 0,
                "reason_codes": []
            }

        decision = {
            "domain": self.domain.value,
            "recommended_decision": "AUTO_REPAIR_CANDIDATE",
            "risk_score": scored_case["risk_score"],
            "reason_codes": scored_case["reason_codes"],
            "requires_prime": 0,
            "requires_quorum": 0
        }

        if scored_case.get("risk_score", 0) > 400:
            self.mark_requires_prime(decision)
            decision["recommended_decision"] = "REQUIRES_PRIME_REVIEW"

        return decision

    async def execute(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {"executed": False, "msg": "Repair application delegated to MetaGovernor"}

    async def emit_lineage(self, case: Dict[str, Any], decision: Dict[str, Any], outcome: Optional[Dict[str, Any]] = None):
        pass
