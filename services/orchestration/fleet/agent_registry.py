from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from libs.db.models.core_models import AgentNode, AgentRole, AgentStatus
from libs.db.repositories.fleet_repository import AgentNodeRepo

class AgentRegistry:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AgentNodeRepo(db)

    def register_agent(self, 
                       name: str, 
                       role: AgentRole, 
                       cluster_id: Optional[uuid.UUID] = None,
                       capabilities: Dict[str, Any] = None) -> AgentNode:
        """Adds a new agent to the fleet registry."""
        agent = AgentNode(
            name=name,
            role=role,
            cluster_id=cluster_id,
            capabilities=capabilities or {},
            status=AgentStatus.IDLE
        )
        return self.repo.save_agent(agent)

    def update_agent_status(self, agent_id: uuid.UUID, status: AgentStatus):
        self.repo.update_status(agent_id, status)

    def get_agents_by_role(self, role: AgentRole) -> List[AgentNode]:
        return self.repo.list_available_agents(role)

    def get_best_candidate(self, role: AgentRole, constraints: Optional[Dict[str, Any]] = None) -> Optional[AgentNode]:
        """
        Selection logic based on trust_score, current_load, and capabilities.
        """
        available = self.repo.list_available_agents(role)
        if not available:
            return None
        
        # Simple heuristic: Highest trust score, then lowest load
        # In Phase 12.2, we could add more complex constraint matching (e.g., language, specific tool access)
        available.sort(key=lambda x: (x.trust_score, -x.current_load), reverse=True)
        
        return available[0]

    def mark_agent_quarantined(self, agent_id: uuid.UUID, reason: str):
        agent = self.repo.get_agent(agent_id)
        if agent:
            agent.status = AgentStatus.QUARANTINED
            agent.capabilities["quarantine_reason"] = reason
            self.db.commit()
