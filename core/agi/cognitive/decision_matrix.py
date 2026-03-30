import json
import re
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from core.agi.schemas import ProblemFrame, ContextPackage, ExecutionPlan, PlanStep, RiskLevel
from core.agi.prompt_blueprints import build_planner_execution_contract

_log = get_logger("agi_decision_matrix")

class DecisionMatrix:
    """
    Bilişsel Çekirdek - Karar Mekanizması (Decision Matrix).
    Algılanan 'ProblemFrame' ve mevcut 'ContextPackage' bilgilerini kullanarak 
    en uygun eylem dizisini (ExecutionPlan) belirler.
    Bu birim, sistemin stratejik planlama ve niyet (intent) gerçekleştirme merkezidir.
    """
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    async def decide(self, frame: ProblemFrame, context: ContextPackage) -> ExecutionPlan:
        """
        Mevcut çerçeve ve bağlam ışığında bir eylem planına karar ver.
        """
        _log.info(f"Karar veriliyor: {frame.objective}")

        prompt = self._build_decision_prompt(frame, context)
        try:
            response = await self.model_orch.complete(
                [{"role": "user", "content": prompt}],
                preferred_agent="architect"
            )
            
            plan_data = self._parse_json_from_response(response)
            
            steps = []
            for s in plan_data.get("steps", []):
                steps.append(PlanStep(
                    step_id=s.get("step_id", "step_0"),
                    agent_id=s.get("agent_id", "architect"),
                    action=s.get("action", "check"),
                    params=s.get("params", {}),
                    dependencies=s.get("dependencies", []),
                    verification_point=s.get("verification_point")
                ))

            return ExecutionPlan(
                goal=frame.objective,
                steps=steps,
                tool_requirements=plan_data.get("tool_requirements", []),
                required_context_refs=plan_data.get("required_context_refs", []),
                fallback_paths=plan_data.get("fallback_paths", {}),
                rollback_conditions=plan_data.get("rollback_conditions", []),
                confidence_estimate=plan_data.get("confidence_estimate", 1.0),
                estimated_risk=RiskLevel(plan_data.get("estimated_risk", frame.risk_level.value))
            )
        except Exception as e:
            _log.error(f"Karar verme/Planlama hatası: {e}")
            # Fallback plan (Direct action)
            return ExecutionPlan(
                goal=frame.objective,
                steps=[PlanStep(step_id="fallback", agent_id="architect", action="execute")],
                estimated_risk=frame.risk_level
            )

    def _build_decision_prompt(self, frame: ProblemFrame, context: ContextPackage) -> str:
        # Planner blueprint'ini 'Decision Matrix' perspektifinden kullan
        return build_planner_execution_contract(frame, context)

    def _parse_json_from_response(self, text: str) -> Dict[str, Any]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}
