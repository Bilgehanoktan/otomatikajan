from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIEnterpriseReadinessAssessment
from .production_readiness_score import ProductionReadinessCalculator

class EnterpriseReadinessAssessor:
    """Performs end-to-end assessment of system readiness."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = ProductionReadinessCalculator()

    async def perform_assessment(self, assessor_name: str) -> UIEnterpriseReadinessAssessment:
        """Executes the full assessment suite and persists results."""
        # 1. Gather metrics (simulated for now, would query DB in real usage)
        metrics = await self._gather_system_metrics()
        
        # 2. Calculate scores
        score = self.calculator.calculate_score(metrics)
        rating = self.calculator.get_rating(score)
        blockers = self.calculator.identify_blockers(metrics)
        
        # 3. Create assessment record
        assessment = UIEnterpriseReadinessAssessment(
            overall_score=score,
            rating=rating,
            monitoring_score=metrics.get("monitoring_coverage", 0.0),
            governance_score=metrics.get("governance_safety", 0.0),
            resilience_score=metrics.get("resilience_status", 0.0),
            audit_score=metrics.get("evidence_completeness", 0.0),
            operations_score=metrics.get("notification_readiness", 0.0),
            assessment_json=metrics,
            blocker_list_json=blockers,
            warning_list_json=self._identify_warnings(metrics),
            assessed_by=assessor_name
        )
        
        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def _gather_system_metrics(self) -> Dict[str, float]:
        """Collects performance and coverage data from the system."""
        # Real implementation would scan models for coverage, pass rates, etc.
        return {
            "monitoring_coverage": 95.0,
            "evidence_completeness": 100.0,
            "repair_reliability": 88.0,
            "pr_review_reliability": 92.0,
            "verifier_mesh_consistency": 94.0,
            "governance_safety": 100.0,
            "rollback_readiness": 100.0,
            "chaos_drill_coverage": 85.0,
            "soak_stability": 98.0,
            "notification_readiness": 90.0,
            "crisis_control_readiness": 100.0,
            "resilience_status": 92.0
        }

    def _identify_warnings(self, metrics: Dict[str, float]) -> List[str]:
        warnings = []
        if metrics.get("repair_reliability", 0.0) < 90:
            warnings.append("Repair reliability is slightly below target (90%).")
        if metrics.get("chaos_drill_coverage", 0.0) < 90:
            warnings.append("Chaos drill coverage could be expanded.")
        return warnings
