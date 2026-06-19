from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import (
    UIRepairProjectProfile, UIRolloutWave, UIRepairCase, UIGAReadinessAssessment, UIEnterpriseRunbook
)
from .sla_slo_tracker import SLASLOTracker
from .ga_readiness_checker import GAReadinessChecker

class MultiProjectDashboardService:
    """Aggregates metrics and status for the enterprise-wide dashboard."""
    
    @staticmethod
    async def get_enterprise_overview(db: AsyncSession):
        # 1. Project Stats
        stmt_total = select(func.count(UIRepairProjectProfile.id))
        total_projects = (await db.execute(stmt_total)).scalar() or 0
        
        stmt_active = select(func.count(UIRepairProjectProfile.id)).where(UIRepairProjectProfile.status == "ACTIVE")
        active_projects = (await db.execute(stmt_active)).scalar() or 0
        
        stmt_blocked = select(func.count(UIRepairProjectProfile.id)).where(UIRepairProjectProfile.status == "BLOCKED")
        blocked_projects = (await db.execute(stmt_blocked)).scalar() or 0
        
        # 2. Wave Stats
        stmt_waves = select(func.count(UIRolloutWave.id)).where(UIRolloutWave.status == "RUNNING")
        active_waves = (await db.execute(stmt_waves)).scalar() or 0
        
        # 3. Case Stats
        stmt_gov = select(func.count(UIRepairCase.id)).where(UIRepairCase.status == "WAITING_GOVERNANCE")
        gov_waiting = (await db.execute(stmt_gov)).scalar() or 0
        
        # 4. Enterprise Metrics
        metrics = await SLASLOTracker.get_enterprise_metrics(db)
        
        # 5. GA Readiness
        ga_assessment = await GAReadinessChecker.get_latest_assessment(db)
        ga_status = ga_assessment.recommendation if ga_assessment else "PENDING"
        
        # 6. Runbook
        stmt_rb = select(UIEnterpriseRunbook).limit(1)
        has_runbook = (await db.execute(stmt_rb)).scalar_one_or_none() is not None
        
        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "blocked_projects": blocked_projects,
            "global_health_score": 98.4, # Mock global score
            "active_waves": active_waves,
            "critical_route_coverage": metrics["critical_route_coverage"],
            "governance_waiting_total": gov_waiting,
            "slo_compliance_rate": metrics["rollback_snapshot_compliance"], # Using rollback as proxy for compliance
            "ga_readiness_status": ga_status,
            "runbook_status": "GENERATED" if has_runbook else "MISSING"
        }
