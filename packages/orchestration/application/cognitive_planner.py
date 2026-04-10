import logging
import uuid
from typing import Any, Dict, List, Optional
from packages.observability.logging import get_logger
from packages.orchestration.domain.models import ProjectTask, TaskStatus, SubTask, RiskLevel, TaskType
from packages.orchestration.agi.schemas import ProblemFrame

_log = get_logger("agi_cognitive_planner")

class CognitivePlanner:
    def __init__(self, model_orch, affective_core, motivation_engine):
        self.model_orch = model_orch
        self.affective = affective_core
        self.motivation = motivation_engine

    async def execute_dialectic_planning(self, task_id: str, title: str, context: str, description: str, affective_state: Optional[Dict[str, float]] = None) -> List[SubTask]:
        from packages.orchestration.application.agent_discovery import build_agents, discover_and_build_specialists
        from packages.orchestration.agi.cognitive.agi_goal_decomposer import agi_goal_decomposer
        from packages.orchestration.agi.governance.watchdog import governance_watchdog
        from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
        from packages.persistence.session import get_db
        
        all_agents = build_agents()
        all_agents.update(discover_and_build_specialists())
        available_agents = [{"id": a.id, "name": a.name, "role": a.role_name} for a in all_agents.values()]
        
        target_role = "architect"
        if "research" in title.lower(): target_role = "deerflow_researcher"
        elif "plan" in title.lower(): target_role = "deerflow_planner"
        
        subtasks = await agi_goal_decomposer.decompose(title, description, available_agents, affective_state, lead_agent_role=target_role)
        
        predicted_violations = await governance_watchdog.predict_violations(subtasks)
        if predicted_violations:
            _log.warning(f"[PLANNER] Predicted violations found: {len(predicted_violations)}. Inhibiting...")
            async with get_db() as db:
                for v in predicted_violations:
                    await synaptic_cortex.save_architectural_inhibition(db=db, rule_id=v.rule_id, target=v.target, description=f"[PREDICTION] {v.description}")
        
        return subtasks
