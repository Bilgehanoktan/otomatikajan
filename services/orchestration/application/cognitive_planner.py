import logging
import uuid
from typing import Any, Dict, List, Optional
from services.observability.logging import get_logger
from services.orchestration.domain.models import ProjectTask, TaskStatus, SubTask, RiskLevel, TaskType
from services.orchestration.agi.schemas import ProblemFrame

_log = get_logger("agi_cognitive_planner")

class CognitivePlanner:
    def __init__(self, model_orch, affective_core, motivation_engine, foresight_cortex=None):
        self.model_orch = model_orch
        self.affective = affective_core
        self.motivation = motivation_engine
        self.foresight = foresight_cortex

    async def execute_dialectic_planning(self, task_id: str, title: str, context: str, description: str, affective_state: Optional[Dict[str, float]] = None) -> List[SubTask]:
        from services.orchestration.application.agent_discovery import build_agents, discover_and_build_specialists
        from services.orchestration.agi.cognitive.agi_goal_decomposer import agi_goal_decomposer
        from services.orchestration.agi.governance.watchdog import governance_watchdog
        from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
        from libs.db.session import get_db
        from services.orchestration.agi.schemas import PlanProposal
        
        all_agents = build_agents()
        all_agents.update(discover_and_build_specialists())
        available_agents = [{"id": a.id, "name": a.name, "role": a.role_name} for a in all_agents.values()]
        
        target_role = "architect"
        if "research" in title.lower(): target_role = "deerflow_researcher"
        elif "plan" in title.lower(): target_role = "deerflow_planner"
        
        subtasks = await agi_goal_decomposer.decompose(title, description, available_agents, affective_state, lead_agent_role=target_role)
        
        # Faz 12.3: Stratejik Öngörü Simülasyonu
        if self.foresight:
            _log.info(f"[PLANNER] Plan simülasyonu başlatılıyor: {title}")
            proposal = PlanProposal(
                task_id=task_id,
                title=title,
                steps=[st.prompt for st in subtasks],
                risk_level=RiskLevel.MEDIUM
            )
            sim_result = await self.foresight.simulate_plan(proposal)
            _log.info(f"[PLANNER] Simülasyon Skoru: {sim_result.get('strategic_alignment_score', 0.0)}")
            
            # Risk uyarısını ilk subtask'e enjekte et
            if sim_result.get("predicted_risks"):
                risks = "\n".join([f"- {r['failure_mode']} ({r['severity']})" for r in sim_result["predicted_risks"]])
                subtasks[0].prompt += f"\n\n### 🛡️ ÖNGÖRÜ UYARISI:\n{risks}"

        predicted_violations = await governance_watchdog.predict_violations(subtasks)
        if predicted_violations:
            _log.warning(f"[PLANNER] Predicted violations found: {len(predicted_violations)}. Inhibiting...")
            async with get_db() as db:
                for v in predicted_violations:
                    await synaptic_cortex.save_architectural_inhibition(db=db, rule_id=v.rule_id, target=v.target, description=f"[PREDICTION] {v.description}")
        
        return subtasks
