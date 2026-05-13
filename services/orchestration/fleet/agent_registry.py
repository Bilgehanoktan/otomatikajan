# from sqlalchemy.orm import Session
from typing import Any, List, Optional, Dict, Any
import uuid
# from libs.db.models.core_models import AgentNode, AgentRole, AgentStatus
# from libs.db.repositories.fleet_repository import AgentNodeRepo

class AgentRegistry:
    def __init__(self, db: Any):
        from libs.db.repositories.fleet_repository import AgentNodeRepo
        self.db = db
        self.repo = AgentNodeRepo(db)

    def register_agent(self, 
                       name: str, 
                       role: Any, 
                       cluster_id: Optional[uuid.UUID] = None,
                       capabilities: Dict[str, Any] = None) -> Any:
        """Adds a new agent to the fleet registry."""
        from libs.db.models.core_models import AgentNode
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
            
            # Phase 12.2: Log to lineage
            from services.governance.lineage_service import LineageService
            import asyncio
            import threading
            
            def run():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(LineageService.log_fleet_event(
                        event_type="AGENT_QUARANTINED",
                        target_id=str(agent.id),
                        details=f"Agent {agent.name} quarantined: {reason}"
                    ))
                    loop.close()
                except Exception as e:
                    pass
                    
            threading.Thread(target=run, daemon=True).start()
            
            self.db.commit()

    def update_agent_reputation(self, agent_id: uuid.UUID, success: bool, impact_factor: float = 1.0):
        """Phase 12.2: Autonomous Reputation System"""
        agent = self.repo.get_agent(agent_id)
        if not agent:
            return
            
        if success:
            agent.success_count += 1
            # Increase trust score, cap at 1.0
            agent.trust_score = min(1.0, agent.trust_score + (0.05 * impact_factor))
        else:
            agent.failure_count += 1
            # Decrease trust score, min 0.0
            agent.trust_score = max(0.0, agent.trust_score - (0.1 * impact_factor))
            
        self.db.commit()
            
        # Automatic Quarantine if trust score drops too low
        if agent.trust_score < 0.3 and agent.status != AgentStatus.QUARANTINED:
            self.mark_agent_quarantined(agent_id, reason="Trust score dropped below critical threshold (0.3)")
