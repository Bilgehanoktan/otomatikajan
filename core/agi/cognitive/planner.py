import json
import re
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from core.agi.schemas import ProblemFrame, ContextPackage, ExecutionPlan, PlanStep, RiskLevel

_log = get_logger("agi_planner")

class CognitivePlanner:
    """
    Bilişsel Çekirdek - Planlama Katmanı.
    ProblemFrame ve ContextPackage'dan 'ExecutionPlan' üretir.
    """
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    async def create_plan(self, frame: ProblemFrame, context: ContextPackage) -> ExecutionPlan:
        _log.info(f"Planlanıyor: {frame.objective}")

        prompt = self._build_planner_prompt(frame, context)
        try:
            response = await self.model_orch.generate(
                prompt,
                task_id=f"plan_{frame.objective[:20]}",
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
            _log.error(f"Planlama hatası: {e}")
            # Fallback plan (Direct action)
            return ExecutionPlan(
                goal=frame.objective,
                steps=[PlanStep(step_id="fallback", agent_id="architect", action="execute")],
                estimated_risk=frame.risk_level
            )

    def _build_planner_prompt(self, frame: ProblemFrame, context: ContextPackage) -> str:
        return f"""
        Aşağıdaki ProblemFrame ve Bağlamı temel alarak adım adım bir 'ExecutionPlan' (DAG tabanlı) oluştur.
        
        Hedef: {frame.objective}
        Risk Seviyesi: {frame.risk_level.value}
        Kısıtlamalar: {frame.constraints}
        Bağlam: {context.working_context}
        İlgili Yetenekler (Skills): {context.relevant_skills}
        
        Yanıtı SADECE aşağıdaki JSON formatında ver:
        {{
            "steps": [
                {{
                    "step_id": "S1",
                    "agent_id": "architect|backend_dev|...",
                    "action": "Açıklama",
                    "params": {{}},
                    "dependencies": [],
                    "verification_point": "Doğrulama kriteri"
                }}
            ],
            "tool_requirements": ["shell", "read", "test", ...],
            "required_context_refs": ["memory_id_1", ...],
            "fallback_paths": {{"S1": "R1"}},
            "rollback_conditions": ["şart 1"],
            "confidence_estimate": 0.0-1.0 float,
            "estimated_risk": "low|medium|high|critical"
        }}
        """

    def _parse_json_from_response(self, text: str) -> Dict[str, Any]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}
