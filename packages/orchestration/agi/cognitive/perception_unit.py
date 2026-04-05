import json
import re
from typing import Dict, Any, Optional
from packages.observability.logging import get_logger
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.orchestration.agi.schemas import UnifiedInput, ProblemFrame, TaskType, RiskLevel

_log = get_logger("agi_perception_unit")

class PerceptionUnit:
    """
    Bilişsel Çekirdek - Algı Katmanı (Perception Unit).
    Ham 'UnifiedInput' girdilerini yüksek seviyeli 'ProblemFrame' (Bilişsel Çerçeve) yapılarına dönüştürür.
    Bu birim, dış dünyadan gelen duyusal verilerin (istekler, loglar, hatalar) anlamlandırılmasından sorumludur.
    """
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    async def perceive(self, inp: UnifiedInput) -> ProblemFrame:
        """
        Girdiyi algıla ve bilişsel bir çerçeve (ProblemFrame) oluştur.
        Faz 22: Proactive Memory Recall eklendi.
        """
        _log.info(f"Algılanıyor: {inp.input_id} (Kaynak: {inp.source_type.value})")

        # --- Faz 22: Proactive Recall (Hafıza Taraması) ---
        past_memories = []
        try:
            from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
            from packages.persistence.session import session_scope
            async with session_scope() as db:
                # Girdi içeriğiyle benzer geçmiş epizotları ara
                past_memories = await synaptic_cortex.search(
                    db, 
                    query=str(inp.raw_payload)[:100], 
                    project_id=str(inp.input_id),
                    top_k=3
                )
        except Exception as e:
            _log.warning(f"Proactive Recall hatası (Algı katmanı): {e}")

        prompt = self._build_perception_prompt(inp, past_memories)
        try:
            response = await self.model_orch.complete(
                [{"role": "user", "content": prompt}],
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
            _log.error(f"Algılama hatası: {e}")
            # Fallback frame
            return ProblemFrame(
                task_type=TaskType.ANALYSIS,
                objective=str(inp.raw_payload)[:200],
                risk_level=RiskLevel.MEDIUM if inp.urgency > 7 else RiskLevel.LOW
            )

    def _build_perception_prompt(self, inp: UnifiedInput, past_memories: Optional[list] = None) -> str:
        memory_str = ""
        if past_memories:
            memory_str = "\nBENZER GEÇMİŞ DENEYİMLER:\n" + "\n".join([f"- {m['body']}" for m in past_memories])

        return f"""
        Aşağıdaki duyusal girdiyi bir 'ProblemFrame' (Bilişsel Çerçeve) nesnesine dönüştür. 
        Sen gelişmiş bir AGI sisteminin 'Algı Birimi' (Perception Unit) parçasısın. 
        {memory_str}
        
        Girdi Türü: {inp.source_type.value}
        Girdi İçeriği: {inp.raw_payload}
        Güven Seviyesi: {inp.trust_level}
        Aciliyet: {inp.urgency}
        ...
        
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
