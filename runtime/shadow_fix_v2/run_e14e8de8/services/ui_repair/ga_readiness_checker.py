import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UIGAReadinessAssessment, UIRepairProjectProfile, UIMonitoringConfig,
    UIPilotFinalReport, UIChaosDrillRun, UIRecoveryProofPack
)
from .sla_slo_tracker import SLASLOTracker

class GAReadinessChecker:
    """Performs automated checks for General Availability readiness."""
    
    @staticmethod
    async def perform_check(db: AsyncSession, assessor: str) -> UIGAReadinessAssessment:
        blockers = []
        warnings = []
        
        # 1. Project Checks
        stmt_p = select(UIRepairProjectProfile).where(UIRepairProjectProfile.status == "ACTIVE")
        res_p = await db.execute(stmt_p)
        active_projects = list(res_p.scalars().all())
        
        if not active_projects:
            # Check for pilot projects if no active
            stmt_pilot = select(UIRepairProjectProfile).where(UIRepairProjectProfile.status == "PILOT")
            res_pilot = await db.execute(stmt_pilot)
            active_projects = list(res_pilot.scalars().all())
            if not active_projects:
                blockers.append("No active or pilot projects found.")

        # 2. Critical Route Coverage
        # (Assuming we have a way to check if all projects have critical routes covered)
        
        # 3. Governance Bypass & Auto-Apply Safety
        metrics = await SLASLOTracker.get_enterprise_metrics(db)
        if metrics["governance_bypass_count"] > 0:
            blockers.append("Governance bypass detected in operational history.")
        if metrics["auto_apply_without_approval"] > 0:
            blockers.append("Auto-apply without approval detected.")
        if metrics["rollback_snapshot_compliance"] < 100:
            blockers.append("Rollback snapshot compliance is not 100%.")

        # 4. Pilot Evidence
        stmt_report = select(UIPilotFinalReport).limit(1)
        if not (await db.execute(stmt_report)).scalar_one_or_none():
            blockers.append("No pilot final report found.")

        # 5. Resilience Evidence
        stmt_proof = select(UIRecoveryProofPack).limit(1)
        if not (await db.execute(stmt_proof)).scalar_one_or_none():
            warnings.append("No recovery proof packs generated yet.")

        # 6. False Negative Rate
        if metrics["false_negative_rate"] > 0.05:
            blockers.append(f"High false negative rate: {metrics['false_negative_rate']*100}%")

        # Recommendation Logic
        score = 100.0
        score -= len(blockers) * 20
        score -= len(warnings) * 5
        score = max(0, score)
        
        recommendation = "GA_READY"
        if blockers:
            recommendation = "NO_GO"
        elif score < 80:
            recommendation = "EXTEND_PILOT"
        elif warnings:
            recommendation = "GA_WITH_WARNINGS"
            
        assessment = UIGAReadinessAssessment(
            id=uuid.uuid4(),
            status="COMPLETED",
            readiness_score=score,
            project_count=len(active_projects),
            passed_projects=len(active_projects) - len(blockers),
            warning_projects=len(warnings),
            blocked_projects=len(blockers),
            blockers_json=blockers,
            warnings_json=warnings,
            recommendation=recommendation,
            assessed_by=assessor,
            created_at=datetime.now(timezone.utc)
        )
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        return assessment

    @staticmethod
    async def get_latest_assessment(db: AsyncSession):
        stmt = select(UIGAReadinessAssessment).order_by(UIGAReadinessAssessment.created_at.desc()).limit(1)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
