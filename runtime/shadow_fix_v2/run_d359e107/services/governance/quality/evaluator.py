"""
Kalite Değerlendirici — Faz 3
Ajan çıktısını (LLMResponse) alır, parse eder ve QualityScorer ile puanlar.
"""

from typing import Tuple
from libs.llm.model_orchestrator import LLMResponse, ModelOrchestrator
from services.governance.quality.output_schema import output_parser, AgentOutput
from services.governance.quality.scorer import quality_scorer, QualityReport

class QualityEvaluator:
    def __init__(self, model_orch: ModelOrchestrator):
        self.llm = model_orch

    async def evaluate(self, response: LLMResponse | AgentOutput) -> QualityReport:
        """
        Ham LLM yanıtını veya zaten parse edilmiş AgentOutput'u değerlendirir.
        """
        if isinstance(response, LLMResponse):
            # 1. Parse et (JSON -> AgentOutput)
            # Not: AgentOutput'un hangi ajandan geldiğini llm_response'dan çıkaramayız, 
            # ancak agent_role bilgisi ModelOrchestrator'da veya subtask'ta mevcuttur.
            # Şimdilik "unknown" veya LLMResponse içindeki model ismini kullanabiliriz.
            agent_id = getattr(response, "agent_role", "agent")
            output = output_parser.parse(agent_id=agent_id, raw=response.content)
        else:
            output = response

        # 2. Puanla
        report = quality_scorer.score(output)
        
        # 3. AgentOutput nesnesini güncelle (referans olarak)
        if isinstance(output, AgentOutput):
            output.quality_score = report.overall
            output.quality_detail = report.to_dict()
            
        return report
