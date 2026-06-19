import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .pilot_mode import PilotRecommendation
from libs.db.models.ui_repair_models import UIPilotRollout, UIPilotMetrics, UIPilotFinalReport

class PilotReportGenerator:
    """Generates a comprehensive final pilot report."""
    
    @staticmethod
    async def generate_report(db: AsyncSession, rollout_id: str):
        stmt_rollout = select(UIPilotRollout).where(UIPilotRollout.id == rollout_id)
        res_rollout = await db.execute(stmt_rollout)
        rollout = res_rollout.scalar_one_or_none()

        stmt_metrics = select(UIPilotMetrics).where(UIPilotMetrics.rollout_id == rollout_id)
        res_metrics = await db.execute(stmt_metrics)
        metrics = res_metrics.scalar_one_or_none()
        
        if not rollout or not metrics:
            return None
            
        # Decision Logic
        recommendation = PilotRecommendation.GO.value
        if metrics.false_negative_count > 0:
            recommendation = PilotRecommendation.GO_WITH_WARNINGS.value
        if metrics.monitoring_runs < 50:
            recommendation = PilotRecommendation.EXTEND_PILOT.value
            
        report_id = str(uuid.uuid4())
        report = UIPilotFinalReport(
            id=report_id,
            rollout_id=rollout_id,
            status="GENERATED",
            recommendation=recommendation,
            readiness_score=85.5, # Placeholder calculation
            executive_summary=f"Pilot rollout '{rollout.name}' completed with mode {rollout.mode}.",
            metrics_json={
                "runs": metrics.monitoring_runs,
                "failures": metrics.failures_detected,
                "prs": metrics.prs_created,
                "approvals": metrics.approved_applies
            },
            risks_json=["Incomplete coverage on auth routes"],
            generated_at=datetime.now(timezone.utc)
        )
        db.add(report)
        await db.commit()
        return report
