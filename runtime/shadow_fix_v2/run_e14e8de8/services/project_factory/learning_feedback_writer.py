import uuid
from typing import List, Optional
from datetime import datetime, timezone
from services.project_factory.models import (
    RiskPattern, 
    LearningRecommendation, 
    LearningMemoryFeedback, 
    LearningSignal, 
    LearningNextAction
)
from services.project_factory.artifacts import write_learning_memory_feedback

def generate_learning_feedback(
    recurring_risks: List[RiskPattern],
    workspace_root: Optional[str] = None
) -> List[LearningRecommendation]:
    
    recommendations = []
    signals = []
    actions = []
    
    for risk in recurring_risks:
        if risk.severity == "HIGH":
            rec_id = f"LRN-PF-{str(uuid.uuid4())[:8].upper()}"
            title = risk.recommended_action
            
            target = "configs/external_project_agent_matrix.yaml" if risk.pattern == "missing_forbidden_action" else "general_sandbox_config"
            
            recommendations.append(LearningRecommendation(
                recommendation_id=rec_id,
                title=title,
                priority=risk.severity,
                target=target,
                suggested_workflow=risk.suggested_workflow or "self_repair_v1"
            ))
            
            signals.append(LearningSignal(
                signal_id=f"PF-SIG-{str(uuid.uuid4())[:8].upper()}",
                type="recurring_risk",
                summary=f"Detected recurring {risk.pattern} ({risk.count} times).",
                confidence=min(0.5 + (risk.count * 0.1), 0.99),
                recommended_policy_update=True,
                target_files=[target]
            ))
            
            actions.append(LearningNextAction(
                type="ceo_suggestion",
                title=title,
                priority=risk.severity
            ))
            
    feedback = LearningMemoryFeedback(
        generated_at=datetime.now(timezone.utc).isoformat(),
        signals=signals,
        next_actions=actions
    )
    
    write_learning_memory_feedback(feedback.model_dump(), workspace_root)
    
    return recommendations
