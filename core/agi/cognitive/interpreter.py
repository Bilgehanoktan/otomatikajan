import json
import re
from typing import Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from core.agi.schemas import UnifiedInput, ProblemFrame, TaskType, RiskLevel

_log = get_logger("agi_interpreter")

class IntentInterpreter:
    """
    Bilişsel Çekirdek - Yorumlama Katmanı.
    UnifiedInput nesnesini 'ProblemFrame' yapısına dönüştürür.
    """
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    async def interpret(self, inp: UnifiedInput) -> ProblemFrame:
        _log.info(f"Yorumlanıyor: {inp.input_id} (Kaynak: {inp.source_type.value})")

        prompt = self._build_interpreter_prompt(inp)
        try:
            response = await self.model_orch.generate(
                prompt,
                task_id=f"interpret_{inp.input_id[:8]}",
                preferred_agent="architect"
            )
            
            frame_data = self._parse_json_from_response(response)
            
            # Enum dönüşümleri ve varsayılanlar
            return ProblemFrame(
                task_type=TaskType(frame_data.get("task_type", "analysis")),
                objective=frame_data.get("objective", "Unknown objective"),
                constraints=frame_data.get("constraints", []),
                risk_level=RiskLevel(frame_data.get("risk_level", "low")),
                evidence_required=frame_data.get("evidence_required", []),
                context_scope=frame_data.get("context_scope", "local"),
                urgency=frame_data.get("urgency", inp.urgency),
                expected_output_type=frame_data.get("expected_output_type", "report"),
                priority=frame_data.get("priority", 5),
                ambiguity_score=frame_data.get("ambiguity_score", 0.0)
            )
        except Exception as e:
            _log.error(f"Yorumlama hatası: {e}")
            # Fallback frame
            return ProblemFrame(
                task_type=TaskType.ANALYSIS,
                objective=str(inp.raw_payload)[:200],
                risk_level=RiskLevel.MEDIUM if inp.urgency > 7 else RiskLevel.LOW
            )

    def _build_interpreter_prompt(self, inp: UnifiedInput) -> str:
        return f"""
        Aşağıdaki girdiyi bir 'ProblemFrame' nesnesine dönüştür. 
        Sistem AGI odaklı bir agent sistemidir. 
        
        Girdi Türü: {inp.source_type.value}
        Girdi İçeriği: {inp.raw_payload}
        Güven Seviyesi: {inp.trust_level}
        Aciliyet: {inp.urgency}
        
        Yanıtı SADECE aşağıdaki JSON formatında ver:
        {{
            "task_type": "analysis|fix|research|suggestion|operation|information",
            "objective": "Net ve kısa hedef",
            "constraints": ["kısıtlama 1", "kısıtlama 2"],
            "risk_level": "low|medium|high|critical",
            "evidence_required": ["test", "log", "diff", "api_result"],
            "context_scope": "local|global|deep",
            "urgency": 1-10 arası tam sayı,
            "expected_output_type": "code|report|plan|data",
            "priority": 1-10 arası tam sayı,
            "ambiguity_score": 0.0-1.0 arası float
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
