import uuid
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from libs.db.session import get_db_ctx
from libs.db.models.core_models import Project, ProjectStatus, SubTask
from libs.db.models.governance_models import GovernorDomain
from services.governance.base_governor import BaseDomainGovernor
from services.observability.logging import get_logger

logger = get_logger("governance.workflow_governor")

class WorkflowGovernor(BaseDomainGovernor):
    """
    Workflow/Project durumlarına odaklanan Domain Governor.
    FAILED, ERROR, PAUSED, stale workflow ve retry bütçelerini denetler.
    """

    def __init__(self):
        super().__init__(domain=GovernorDomain.WORKFLOW)

    async def build_case(self, project_id: UUID) -> Dict[str, Any]:
        async with get_db_ctx() as session:
            res = await session.execute(select(Project).where(Project.id == project_id))
            project = res.scalar_one_or_none()
            if not project:
                return {}

            step_res = await session.execute(
                select(
                    func.count(SubTask.id).label("total"),
                    func.count(SubTask.id).filter(SubTask.status == ProjectStatus.COMPLETED).label("done"),
                    func.count(SubTask.id).filter(
                        SubTask.status.in_([ProjectStatus.ERROR, ProjectStatus.FAILED])
                    ).label("failed"),
                ).where(SubTask.project_id == project_id)
            )
            step_row = step_res.one()

            now = datetime.now(timezone.utc)
            ref_time = project.updated_at or project.created_at
            if ref_time and ref_time.tzinfo is None:
                ref_time = ref_time.replace(tzinfo=timezone.utc)
            
            staleness = (now - ref_time).total_seconds() / 3600.0 if ref_time else 0.0

            return {
                "project_id": project_id,
                "status": project.status.value if hasattr(project.status, "value") else str(project.status),
                "retry_count": project.retry_count or 0,
                "total_steps": step_row.total,
                "failed_steps": step_row.failed,
                "staleness_hours": staleness,
                "priority": project.priority.value if hasattr(project.priority, "value") else str(project.priority),
            }

    async def score_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        if not case: return {}
        
        score = 0.0
        reasons = []

        if case.get("staleness_hours", 0) > 24:
            score += 0.3
            reasons.append("STALE_WORKFLOW")

        if case.get("failed_steps", 0) > 0:
            score += 0.2
            reasons.append("HAS_FAILED_STEPS")

        if case.get("retry_count", 0) >= 3:
            score += 0.4
            reasons.append("RETRY_BUDGET_EXHAUSTED")

        case["risk_score"] = self.normalize_risk_score(score)
        case["reason_codes"] = self.normalize_reason_codes(reasons)
        return case

    async def decide(self, scored_case: Dict[str, Any]) -> Dict[str, Any]:
        if not scored_case: return {}
        
        risk = scored_case["risk_score"]
        decision = {
            "domain": self.domain.value,
            "recommended_decision": "NO_ACTION",
            "risk_score": risk,
            "reason_codes": scored_case["reason_codes"],
            "requires_prime": 0,
            "requires_quorum": 0
        }

        status = scored_case.get("status")
        if status in ("FAILED", "ERROR"):
            if scored_case.get("retry_count", 0) < 3:
                decision["recommended_decision"] = "AUTO_REPLAY_CANDIDATE"
            else:
                self.mark_requires_prime(decision)
        
        if scored_case.get("staleness_hours", 0) > 48:
            decision["recommended_decision"] = "ARCHIVE_STALE"

        return decision

    async def execute(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {"executed": False, "msg": "Execution delegated to MetaGovernor"}

    async def emit_lineage(self, case: Dict[str, Any], decision: Dict[str, Any], outcome: Optional[Dict[str, Any]] = None):
        # Lineage integration will be handled in later steps
        pass
