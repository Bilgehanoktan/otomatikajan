from typing import Dict, Any, List
# SQLAlchemy and Model imports moved to local scopes to prevent Phase 13.04 startup hangs in Python 3.14+
# from sqlalchemy import select, func, and_
# from libs.db.models.core_models import SystemImprovement, OperationalIncident, Project
from datetime import datetime, timezone, timedelta
from uuid import UUID

class ImprovementMetricsService:
    def __init__(self, db_session):
        self.db = db_session

    async def get_canary_stats(self, days: int = 7) -> Dict[str, Any]:
        """Calculates canary evidence depth."""
        from sqlalchemy import select, func, and_
        from libs.db.models.core_models import SystemImprovement
        
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total patches
        total_stmt = select(func.count(SystemImprovement.id)).where(SystemImprovement.created_at >= since)
        total_result = await self.db.execute(total_stmt)
        total_count = total_result.scalar() or 0

        # Applied/Promoted
        promoted_stmt = select(func.count(SystemImprovement.id)).where(
            and_(SystemImprovement.created_at >= since, SystemImprovement.status == "applied")
        )
        promoted_count = (await self.db.execute(promoted_stmt)).scalar() or 0

        # Rolled back
        rollback_stmt = select(func.count(SystemImprovement.id)).where(
            and_(SystemImprovement.created_at >= since, SystemImprovement.status == "rolled_back")
        )
        rollback_count = (await self.db.execute(rollback_stmt)).scalar() or 0

        # Active Canary
        active_stmt = select(func.count(SystemImprovement.id)).where(SystemImprovement.status == "canary")
        active_count = (await self.db.execute(active_stmt)).scalar() or 0

        success_rate = (promoted_count / (promoted_count + rollback_count) * 100) if (promoted_count + rollback_count) > 0 else 0

        return {
            "period_days": days,
            "total_patches": total_count,
            "promoted": promoted_count,
            "rolled_back": rollback_count,
            "active_canary": active_count,
            "success_rate": round(success_rate, 2),
            "rollback_rate": round(100 - success_rate, 2) if (promoted_count + rollback_count) > 0 else 0
        }

    async def get_risk_calibration_data(self) -> Dict[str, Any]:
        """Analyzes risk scoring effectiveness."""
        from sqlalchemy import select, func
        from libs.db.models.core_models import SystemImprovement
        
        # Average risk of rolled back patches
        rb_risk_stmt = select(func.avg(SystemImprovement.risk_score)).where(SystemImprovement.status == "rolled_back")
        rb_avg_risk = (await self.db.execute(rb_risk_stmt)).scalar() or 0.0

        # Average risk of promoted patches
        pr_risk_stmt = select(func.avg(SystemImprovement.risk_score)).where(SystemImprovement.status == "applied")
        pr_avg_risk = (await self.db.execute(pr_risk_stmt)).scalar() or 0.0

        return {
            "avg_risk_promoted": round(pr_avg_risk, 3),
            "avg_risk_rolled_back": round(rb_avg_risk, 3),
            "current_auto_apply_threshold": 0.25,
            "current_high_risk_threshold": 0.75
        }

    async def get_pilot_performance(self) -> Dict[str, Any]:
        """Gathers Pilot KPI Baselines."""
        from sqlalchemy import select, func
        from libs.db.models.core_models import SystemImprovement, OperationalIncident
        
        # MTTR: Mean Time to Resolution (Incident created -> Patch applied)
        # Simplified: OperationalIncident.created_at vs SystemImprovement.applied_at
        
        # This requires joining OperationalIncident -> ImprovementOpportunity -> SystemImprovement
        # For now, let's look at incident resolution times.
        inc_res_stmt = select(
            func.avg(func.extract('epoch', OperationalIncident.resolved_at - OperationalIncident.created_at))
        ).where(OperationalIncident.status == "resolved")
        
        avg_mttr_s = (await self.db.execute(inc_res_stmt)).scalar() or 0.0

        return {
            "avg_mttr_minutes": round(avg_mttr_s / 60, 2),
            "total_incidents": (await self.db.execute(select(func.count(OperationalIncident.id)))).scalar() or 0,
            "resolved_incidents": (await self.db.execute(select(func.count(OperationalIncident.id)).where(OperationalIncident.status == "resolved"))).scalar() or 0,
            "human_in_the_loop_count": (await self.db.execute(select(func.count(SystemImprovement.id)).where(SystemImprovement.risk_score >= 0.25))).scalar() or 0
        }
