import json
import re
from typing import List, Optional, Dict, Any
from core.agi.schemas import ExecutionPlan, PlanStep, RiskLevel
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_consensus_manager")

class ConsensusManager:
    """
    Cognitive Core (Katman 3): Ensemble Reasoning.
    Birden fazla ajan planını karşılaştırıp 'Ortak Akıl' (Consensus) oluşturur.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def resolve(self, proposals: List[Any], context: str) -> Any:
        """
        Alternatif planları analiz eder ve en sağlam olanı seçer veya hibritleştirir.
        Faz 19: Tartışma (Debate) sonuçlarını dikkate alarak karara bağlar.
        """
        if not proposals:
            raise ValueError("No plan proposals provided for consensus.")
        if len(proposals) == 1:
            return proposals[0]

        _log.info(f"Konsensüs Süreci (Dialectic) Başlatıldı: {len(proposals)} plan karşılaştırılıyor.")
        
        # 1. Hazırlık: Planları ve Tartışma Notlarını Topla
        proposals_summary = []
        for p in proposals:
            meta = getattr(p, "metadata", {})
            proposals_summary.append({
                "agent": p.agent_id,
                "content": p.content,
                "critique_from": meta.get("critique_from"),
                "critique_points": meta.get("critique_points")
            })
        
        prompt = f"""
        Aşağıdaki hedef için önerilen ve BİRBİRİYLE TARTIŞMIŞ {len(proposals)} farklı planı değerlendir.
        Bazı planlar diğer uzmanlar tarafından eleştirildi ve revize edildi.
        
        BAĞLAM: {context[:500]}
        
        TARTIŞMA SONUÇLARI:
        {json.dumps(proposals_summary, default=str, indent=2)}
        
        Görevi en güvenli, en verimli ve eleştirileri en iyi karşılayan HİBRİT PLANI oluştur.
        SADECE planın içeriğini (adım adım) döndür.
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Diyalektik Konsensüs Yöneticisisin. En rasyonel sentezi yap."
            )
            
            # TODO: Gerçek bir merge işlemi eklenebilir. Şimdilik sentezlenen içeriği birinci plana ata.
            proposals[0].content = response.content
            return proposals[0] 

        except Exception as e:
            _log.error(f"Consensus resolve hatası (Dialectic): {e}")
            return proposals[0]

# Singleton
consensus_manager = ConsensusManager()
