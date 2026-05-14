from typing import Dict, Any, List

class ProductionReadinessCalculator:
    """Calculates readiness scores based on system metrics and assessment results."""
    
    WEIGHTS = {
        "monitoring_coverage": 0.15,
        "evidence_completeness": 0.10,
        "repair_reliability": 0.10,
        "pr_review_reliability": 0.10,
        "verifier_mesh_consistency": 0.10,
        "governance_safety": 0.15,
        "rollback_readiness": 0.10,
        "chaos_drill_coverage": 0.05,
        "soak_stability": 0.05,
        "notification_readiness": 0.05,
        "crisis_control_readiness": 0.05
    }

    def calculate_score(self, metrics: Dict[str, float]) -> float:
        """Calculates a weighted score from 0 to 100."""
        total_score = 0.0
        for key, weight in self.WEIGHTS.items():
            val = metrics.get(key, 0.0)
            total_score += val * weight
        return round(total_score, 2)

    def get_rating(self, score: float) -> str:
        """Maps score to enterprise rating."""
        if score >= 90:
            return "Enterprise Ready"
        elif score >= 75:
            return "Ready with Warnings"
        elif score >= 60:
            return "Pilot Only"
        elif score >= 40:
            return "Not Production Ready"
        else:
            return "Blocked"

    def identify_blockers(self, metrics: Dict[str, float]) -> List[str]:
        """Identifies critical blockers based on low scores in key areas."""
        blockers = []
        if metrics.get("governance_safety", 0.0) < 90:
            blockers.append("Governance boundary safety is below critical threshold.")
        if metrics.get("monitoring_coverage", 0.0) < 80:
            blockers.append("Critical route monitoring coverage is insufficient.")
        if metrics.get("evidence_completeness", 0.0) < 90:
            blockers.append("Non-repudiable evidence chain is incomplete.")
        if metrics.get("rollback_readiness", 0.0) < 100:
            blockers.append("Rollback mechanism is not fully validated.")
        return blockers
