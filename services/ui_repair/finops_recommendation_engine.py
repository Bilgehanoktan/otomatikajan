import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIFinOpsRecommendation, UICostAnomaly, UIBudgetPolicy
from .cost_attribution_service import CostAttributionService

class FinOpsRecommendationEngine:
    """Generates automated cost-saving suggestions."""
    
    @staticmethod
    async def generate_recommendations(db: AsyncSession, project_key: str) -> List[UIFinOpsRecommendation]:
        recommendations = []
        
        # 1. Check for chronic high-cost operation types
        op_costs = await CostAttributionService.get_operation_attribution(db, days=7)
        for op in op_costs:
            if op["operation_type"] == "OPENSWE_REPAIR" and op["total_cost"] > 50:
                recommendations.append(UIFinOpsRecommendation(
                    id=uuid.uuid4(),
                    project_key=project_key,
                    recommendation_type="disable_auto_repair_for_low_value_routes",
                    priority="MEDIUM",
                    title="Optimize Expensive Repair Loops",
                    description=f"Repair operations cost ${op['total_cost']:.2f} in the last 7 days. Consider disabling auto-repair for non-critical routes.",
                    expected_savings_usd=op["total_cost"] * 0.2,
                    risk_impact="MEDIUM",
                    status="PENDING",
                    created_at=datetime.now(timezone.utc)
                ))
                
        # 2. Check for monitoring frequency
        # (Simplified: if monitoring cost > $20/week, suggest reducing frequency)
        for op in op_costs:
            if op["operation_type"] == "MONITORING_RUN" and op["total_cost"] > 20:
                 recommendations.append(UIFinOpsRecommendation(
                    id=uuid.uuid4(),
                    project_key=project_key,
                    recommendation_type="reduce_monitoring_frequency",
                    priority="LOW",
                    title="Reduce Monitoring Frequency",
                    description="Monitoring runs are consuming significant budget. Consider increasing the interval for non-critical routes.",
                    expected_savings_usd=op["total_cost"] * 0.3,
                    risk_impact="LOW",
                    status="PENDING",
                    created_at=datetime.now(timezone.utc)
                ))
        
        if recommendations:
            for r in recommendations:
                db.add(r)
            await db.commit()
            for r in recommendations:
                await db.refresh(r)
                
        return recommendations

    @staticmethod
    async def list_recommendations(db: AsyncSession, project_key: Optional[str] = None) -> List[UIFinOpsRecommendation]:
        stmt = select(UIFinOpsRecommendation).order_by(UIFinOpsRecommendation.created_at.desc())
        if project_key:
            stmt = stmt.where(UIFinOpsRecommendation.project_key == project_key)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_recommendation_status(db: AsyncSession, rec_id: str, status: str) -> Optional[UIFinOpsRecommendation]:
        stmt = select(UIFinOpsRecommendation).where(UIFinOpsRecommendation.id == rec_id)
        result = await db.execute(stmt)
        rec = result.scalar_one_or_none()
        if rec:
            rec.status = status
            if status == "APPLIED":
                rec.applied_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(rec)
        return rec
