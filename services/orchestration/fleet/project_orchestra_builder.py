from typing import List, Dict, Any
from libs.db.models.core_models import Project, AgentRole
import uuid

class ProjectOrchestraBuilder:
    def __init__(self):
        # Default team templates
        self.templates = {
            "standard": [AgentRole.PLANNER, AgentRole.EXECUTOR, AgentRole.REVIEWER],
            "bugfix": [AgentRole.PLANNER, AgentRole.EXECUTOR, AgentRole.REVIEWER],
            "high_risk_repair": [AgentRole.PLANNER, AgentRole.REPAIRER, AgentRole.REVIEWER, AgentRole.GOVERNOR],
            "policy_evolution": [AgentRole.PLANNER, AgentRole.AUDITOR, AgentRole.GOVERNOR, AgentRole.SYNTHESIZER],
            "audit_only": [AgentRole.AUDITOR, AgentRole.REVIEWER]
        }

    def infer_required_roles(self, project: Project) -> List[AgentRole]:
        """Determines the required agent roles based on project title/description or type."""
        desc = (project.description or "").lower()
        title = project.title.lower()
        
        if "repair" in desc or "fix" in title or "bug" in title:
            if project.priority == "CRITICAL" or project.priority == "HIGH":
                return self.templates["high_risk_repair"]
            return self.templates["bugfix"]
            
        if "policy" in desc or "evolution" in desc:
            return self.templates["policy_evolution"]
            
        if "audit" in desc or "verify" in desc:
            return self.templates["audit_only"]
            
        return self.templates["standard"]

    def estimate_team_cost(self, roles: List[AgentRole]) -> float:
        """Rough estimation of cost based on team size and roles."""
        # Baseline costs for different roles
        role_weights = {
            AgentRole.PLANNER: 1.0,
            AgentRole.EXECUTOR: 1.5,
            AgentRole.REVIEWER: 0.8,
            AgentRole.REPAIRER: 2.0,
            AgentRole.GOVERNOR: 2.5,
            AgentRole.AUDITOR: 1.2,
            AgentRole.SYNTHESIZER: 1.5
        }
        return sum(role_weights.get(role, 1.0) for role in roles)
