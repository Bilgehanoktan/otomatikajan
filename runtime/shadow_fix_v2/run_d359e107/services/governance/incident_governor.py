import uuid
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy import select, and_
from libs.db.session import get_db_ctx
from libs.db.models.core_models import OperationalIncident
from libs.db.models.governance_models import GovernorDomain
from services.governance.base_governor import BaseDomainGovernor
from services.observability.logging import get_logger

logger = get_logger("governance.incident_governor")

class IncidentGovernor(BaseDomainGovernor):
    """
    Operasyonel olaylara (Incident) odaklanan Domain Governor.
    Severity, recurrence ve safety lock durumlarını denetler.
    """

    def __init__(self):
        super().__init__(domain=GovernorDomain.INCIDENT)

    async def build_case(self, project_id: UUID) -> Dict[str, Any]:
        async with get_db_ctx() as session:
            res = await session.execute(
                select(OperationalIncident)
                .where(and_(
                    OperationalIncident.project_id == project_id,
                    OperationalIncident.status.in_(["open", "investigating"])
                ))
            )
            incidents = res.scalars().all()
            
            incident_data = []
            max_severity = "LOW"
            severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            
            for inc in incidents:
                sev = (inc.severity or "LOW").upper()
                if severity_map.get(sev, 0) > severity_map.get(max_severity, 0):
                    max_severity = sev
                
                incident_data.append({
                    "id": str(inc.id),
                    "type": inc.incident_type,
                    "severity": sev,
                    "message": inc.message
                })

            return {
                "project_id": project_id,
                "incidents": incident_data,
                "max_severity": max_severity,
                "incident_count": len(incident_data)
            }

    async def score_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        if not case or not case.get("incidents"):
            return {"risk_score": 0, "reason_codes": []}

        score = 0.0
        reasons = []
        
        sev = case.get("max_severity", "LOW")
        if sev == "CRITICAL":
            score = 0.9
            reasons.append("CRITICAL_INCIDENT_OPEN")
        elif sev == "HIGH":
            score = 0.6
            reasons.append("HIGH_SEVERITY_INCIDENT")
        elif sev == "MEDIUM":
            score = 0.3
            reasons.append("MEDIUM_SEVERITY_INCIDENT")
        else:
            score = 0.1
            reasons.append("MINOR_INCIDENTS_OPEN")

        case["risk_score"] = self.normalize_risk_score(score)
        case["reason_codes"] = self.normalize_reason_codes(reasons)
        return case

    async def decide(self, scored_case: Dict[str, Any]) -> Dict[str, Any]:
        if not scored_case or not scored_case.get("incidents"):
            return {
                "domain": self.domain.value,
                "recommended_decision": "NO_ACTION",
                "risk_score": 0,
                "reason_codes": []
            }

        decision = {
            "domain": self.domain.value,
            "recommended_decision": "REQUIRES_HUMAN_CONTEXT",
            "risk_score": scored_case["risk_score"],
            "reason_codes": scored_case["reason_codes"],
            "requires_prime": 0,
            "requires_quorum": 0
        }

        if scored_case.get("max_severity") in ("CRITICAL", "HIGH"):
            self.mark_requires_prime(decision)
            decision["recommended_decision"] = "REQUIRES_PRIME_REVIEW"

        return decision

    async def execute(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {"executed": False, "msg": "Incident handling delegated to MetaGovernor"}

    async def emit_lineage(self, case: Dict[str, Any], decision: Dict[str, Any], outcome: Optional[Dict[str, Any]] = None):
        pass
