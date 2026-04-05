import json
from typing import List, Optional, Dict, Any
from llm.model_orchestrator import ModelOrchestrator
from packages.orchestration.agi.schemas import PlanProposal
from observability.logging import get_logger

_log = get_logger("agi_debate_manager")

class DebateManager:
    """
    Cognitive Core (Katman 16): Inter-Agent Cognitive Debate.
    Ajanlar arası diyalektiği yönetir. 'Consensus' öncesi 'Critique' (Eleştiri) adımı ekler.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def argue(self, proposals: List[PlanProposal], context: str) -> List[PlanProposal]:
        """
        Gelen planları "Çapraz Sorguya" (Cross-Review) alır.
        Bir uzmanın planını diğer uzmanlara eleştirtir.
        """
        if len(proposals) < 2:
            return proposals
        
        _log.info(f"Bilişsel Tartışma (Debate) başlatılıyor... Plan Sayısı: {len(proposals)}")
        
        debated_proposals = []
        for i, p in enumerate(proposals):
            # Diğer ajanın planını eleştirecek bir 'Reviewer' seç (basitleştirilmiş: sıradaki ajan)
            reviewer_proposal = proposals[(i + 1) % len(proposals)]
            
            critique = await self._get_critique(p, reviewer_proposal.agent_id, context)
            if critique:
                _log.info(f"TARTIŞMA: {reviewer_proposal.agent_id} -> {p.agent_id} eleştirisi yapıldı.")
                # Planı eleştiriye göre güncelle
                revised_content = await self._revise_plan(p, critique, context)
                p.content = revised_content
                p.metadata = p.metadata or {}
                p.metadata["critique_from"] = reviewer_proposal.agent_id
                p.metadata["critique_points"] = critique
                
            debated_proposals.append(p)
            
        return debated_proposals

    async def _get_critique(self, target_plan: PlanProposal, reviewer_id: str, context: str) -> Optional[str]:
        """Bir ajandan diğerinin planı için eleştiri alır."""
        prompt = f"""
        Uzman Ajan: {reviewer_id}
        Hedef Plan (Agent: {target_plan.agent_id}):
        {target_plan.content}
        
        Lütfen bu planı KENDİ UZMANLIĞIN çerçevesinde eleştir. 
        Eğer plan hataya (error), güvenlik açığına (security risk) veya performans sorununa yol açacak bir adım içeriyorsa belirt.
        Sadece eleştirilerini (maddeler halinde) döndür.
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role=reviewer_id,
                prompt=prompt,
                system_prompt="Sen bir Bilişsel Eleştirmen (Cognitive Critic) olarak rasyonel eleştiri yapmalısın."
            )
            return response.content
        except Exception:
            return None

    async def _revise_plan(self, plan: PlanProposal, critique: str, context: str) -> str:
        """Eleştiriye göre planı otonom revize eder."""
        prompt = f"""
        Mevcut Plan ({plan.agent_id}):
        {plan.content}
        
        Alınan Uzman Eleştirisi:
        {critique}
        
        Lütfen planını bu eleştirileri DİKKATE ALARAK revize et. Planın Hatalardan (Zero-Error) arındırılmış olmalı.
        Sadece yeni plan içeriğini döndür.
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role=plan.agent_id,
                prompt=prompt,
                system_prompt="Eleştirileri yapıcı bulup planını mükemmelleştir."
            )
            return response.content
        except Exception:
            return plan.content

# --- Singleton ---
debate_manager = DebateManager()
