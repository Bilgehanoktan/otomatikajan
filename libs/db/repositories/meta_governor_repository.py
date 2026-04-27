import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import (
    GovernorConflictRecord, MetaGovernorDecisionRecord, 
    GovernorDomain, GovernorConflictType
)

class GovernorConflictRepo:
    @staticmethod
    async def save_conflict(db: AsyncSession, project_id: uuid.UUID, conflict_data: Dict[str, Any]) -> GovernorConflictRecord:
        record = GovernorConflictRecord(
            project_id=project_id,
            domain_a=conflict_data["domain_a"],
            domain_b=conflict_data["domain_b"],
            decision_a=conflict_data["decision_a"],
            decision_b=conflict_data["decision_b"],
            conflict_type=conflict_data["conflict_type"],
            conflict_summary=conflict_data["summary"],
            status="open"
        )
        db.add(record)
        return record

    @staticmethod
    async def list_conflicts(db: AsyncSession, project_id: Optional[uuid.UUID] = None, status: str = "open") -> List[GovernorConflictRecord]:
        stmt = select(GovernorConflictRecord).where(GovernorConflictRecord.status == status)
        if project_id:
            stmt = stmt.where(GovernorConflictRecord.project_id == project_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_conflict(db: AsyncSession, conflict_id: uuid.UUID) -> bool:
        from datetime import datetime, timezone
        stmt = (
            update(GovernorConflictRecord)
            .where(GovernorConflictRecord.id == conflict_id)
            .values(status="resolved", resolved_at=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        return True

class MetaGovernorRepo:
    @staticmethod
    async def save_meta_decision(db: AsyncSession, 
                                project_id: uuid.UUID, 
                                final_decision: Dict[str, Any],
                                constraints: List[str]) -> MetaGovernorDecisionRecord:
        record = MetaGovernorDecisionRecord(
            project_id=project_id,
            winning_domain=final_decision.get("domain"),
            final_decision=final_decision["recommended_decision"],
            final_risk_class=MetaGovernorRepo._calculate_risk_class(final_decision["risk_score"]),
            reason_codes=final_decision.get("reason_codes", []),
            applied_constraints=constraints
        )
        db.add(record)
        return record

    @staticmethod
    def _calculate_risk_class(score: int) -> str:
        if score >= 700: return "CRITICAL"
        if score >= 450: return "HIGH"
        if score >= 200: return "MEDIUM"
        return "LOW"

    @staticmethod
    async def list_meta_decisions(db: AsyncSession, project_id: Optional[uuid.UUID] = None, limit: int = 20) -> List[MetaGovernorDecisionRecord]:
        stmt = select(MetaGovernorDecisionRecord).order_by(MetaGovernorDecisionRecord.created_at.desc()).limit(limit)
        if project_id:
            stmt = stmt.where(MetaGovernorDecisionRecord.project_id == project_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())
