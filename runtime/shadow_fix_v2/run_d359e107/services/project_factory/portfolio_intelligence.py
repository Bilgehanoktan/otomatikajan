import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from services.project_factory.models import (
    RunIntelligenceRequest, 
    CEOSuggestionsPublishRequest,
    PortfolioIntelligence,
    ArchiveIndex,
    CEOSuggestion
)
from services.project_factory.artifacts import (
    load_archive_index, 
    write_portfolio_intelligence,
    load_portfolio_intelligence,
    write_ceo_learning_suggestions
)
from services.project_factory.portfolio_intelligence_logs import log_portfolio_intelligence_run
from services.project_factory.risk_pattern_miner import mine_risk_patterns
from services.project_factory.template_performance_analyzer import analyze_template_performance
from services.project_factory.agent_performance_analyzer import analyze_agent_performance
from services.project_factory.learning_feedback_writer import generate_learning_feedback

def run_portfolio_intelligence(request: RunIntelligenceRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    index_data = load_archive_index(workspace_root)
    if not index_data:
        raise ValueError("archive_index.json not found. Run Portfolio rebuild first.")
        
    archive = ArchiveIndex(**index_data)
    
    # 1. Mine Risk Patterns
    risks = mine_risk_patterns(archive, workspace_root)
    
    # 2. Analyze Template Performance
    templates = analyze_template_performance(archive, workspace_root)
    
    # 3. Analyze Agent Performance
    agents = analyze_agent_performance(archive, workspace_root)
    
    # 4. Generate Learning Recommendations & Feedback Artifact
    recommendations = generate_learning_feedback(risks, workspace_root)
    
    # 5. Build Portfolio Intelligence
    avg_q = 0.0
    avg_r = 0.0
    if templates:
        avg_q = round(sum(t.average_quality_score for t in templates) / len(templates), 1)
        avg_r = round(sum(t.average_risk_score for t in templates) / len(templates), 1)
        
    intel = PortfolioIntelligence(
        generated_at=datetime.now(timezone.utc).isoformat(),
        portfolio_size=archive.total_projects,
        closed_projects=archive.closed_projects,
        blocked_projects=archive.blocked_projects,
        average_quality_score=avg_q,
        average_risk_score=avg_r,
        recurring_risks=risks,
        template_performance=templates,
        agent_performance=agents,
        learning_recommendations=recommendations
    )
    
    write_portfolio_intelligence(intel.model_dump(), workspace_root)
    
    # 6. Log Run
    log_portfolio_intelligence_run(
        operator_id=request.operator_id,
        rationale=request.rationale,
        portfolio_size=archive.total_projects,
        recommendation_count=len(recommendations),
        workspace_root=workspace_root
    )
    
    return {
        "status": "success",
        "intelligence": intel.model_dump()
    }

def publish_ceo_suggestions(request: CEOSuggestionsPublishRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    intel_data = load_portfolio_intelligence(workspace_root)
    if not intel_data:
        raise ValueError("portfolio_intelligence.json not found. Run Intelligence first.")
        
    intel = PortfolioIntelligence(**intel_data)
    
    suggestions: List[CEOSuggestion] = []
    
    for rec in intel.learning_recommendations:
        suggestions.append(CEOSuggestion(
            suggestion_id=f"CEO-SUG-{str(uuid.uuid4())[:8].upper()}",
            title=rec.title,
            description=f"Action required for target: {rec.target}. Suggested workflow: {rec.suggested_workflow}",
            priority=rec.priority
        ))
        
    write_ceo_learning_suggestions({"suggestions": [s.model_dump() for s in suggestions]}, workspace_root)
    
    return {
        "status": "success",
        "message": "CEO suggestions published successfully as artifact.",
        "published_count": len(suggestions)
    }
