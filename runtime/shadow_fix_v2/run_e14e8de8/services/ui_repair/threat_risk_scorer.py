import logging
from typing import Dict, Any, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIAttackPath, UIThreatMitigation

logger = logging.getLogger(__name__)

class ThreatRiskScorer:
    """Phase 23: Logic for calculating multidimensional risk scores for attack paths."""
    
    @staticmethod
    def calculate_path_risk(path: UIAttackPath) -> float:
        """
        Calculates a risk score based on feasibility, impact, and asset criticality.
        Formula: (Feasibility * 0.4) + (Impact * 0.6) adjusted by criticality multiplier.
        """
        base_score = (path.feasibility * 0.4) + (path.impact * 0.6)
        
        # Severity multiplier
        multiplier = 1.0
        if path.severity == "CRITICAL": multiplier = 1.2
        elif path.severity == "HIGH": multiplier = 1.1
        elif path.severity == "LOW": multiplier = 0.8
        
        final_score = min(1.0, base_score * multiplier)
        return round(final_score, 2)

class MitigationRecommender:
    """Phase 23: Suggests security improvements for identified attack paths."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def recommend_mitigations(self, path: UIAttackPath) -> List[UIThreatMitigation]:
        """
        Generates mitigation recommendations tailored to the attack path type.
        """
        recommendations = []
        
        if path.severity in ["HIGH", "CRITICAL"]:
            # Generic but high-impact recommendation
            mit = UIThreatMitigation(
                attack_path_id=path.id,
                mitigation_type="tighten_policy",
                recommendation=f"Restrict access pattern for {path.source_asset_key} targeting {path.target_asset_key}.",
                status="PENDING"
            )
            recommendations.append(mit)
            
            # Specific recommendation for isolation bypass
            if "ISOLATION" in path.path_type:
                mit2 = UIThreatMitigation(
                    attack_path_id=path.id,
                    mitigation_type="strengthen_tenant_isolation",
                    recommendation="Implement strict cryptographic binding for cross-tenant mesh routing headers.",
                    status="PENDING"
                )
                recommendations.append(mit2)
                
        for r in recommendations:
            self.session.add(r)
            
        await self.session.commit()
        return recommendations
