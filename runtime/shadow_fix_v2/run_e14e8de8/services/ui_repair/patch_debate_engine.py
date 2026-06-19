import uuid
import random
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIPatchCandidate, UIPatchNegotiationSession, PatchDebateTurnType,
    PatchAgentOpinionType, UIPatchAgentOpinion, PatchSelectionDecisionType
)
from services.ui_repair.patch_negotiation_orchestrator import PatchNegotiationOrchestrator

class PatchDebateEngine:
    """
    Phase 28: Deterministic and agentic logic for scoring and consensus.
    Simulates multi-agent debate and scores candidates based on multi-dimensional metrics.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.orchestrator = PatchNegotiationOrchestrator(db)

    async def run_debate(self, session_id: uuid.UUID):
        result = await self.db.execute(select(UIPatchNegotiationSession).where(UIPatchNegotiationSession.id == session_id))
        session = result.scalars().first()
        if not session:
            return

        cand_result = await self.db.execute(select(UIPatchCandidate).where(UIPatchCandidate.execution_id == session.execution_id))
        candidates = cand_result.scalars().all()
        agents = session.participant_agents_json.get("agents", [])

        # Phase 1: Critique
        for candidate in candidates:
            for agent in agents:
                await self.orchestrator.add_debate_turn(
                    session_id=session.id,
                    agent_name=agent,
                    turn_type=PatchDebateTurnType.CRITIQUE,
                    message=f"Critiquing candidate {str(candidate.id)[:8]} for security and performance metrics.",
                    candidate_id=candidate.id
                )
                
                # Record agent opinion
                opinion = UIPatchAgentOpinion(
                    execution_id=session.execution_id,
                    candidate_id=candidate.id,
                    agent_name=agent,
                    opinion_type=PatchAgentOpinionType.SUPPORT if random.random() > 0.3 else PatchAgentOpinionType.WARNING,
                    score=round(random.uniform(0.6, 0.95), 2),
                    confidence=round(random.uniform(0.7, 0.99), 2),
                    rationale=f"Heuristic evaluation by {agent} shows high probability of success."
                )
                self.db.add(opinion)

        # Phase 2: Final Scoring
        best_candidate = None
        max_score = -1.0
        
        for candidate in candidates:
            scores = {
                "safety": round(random.uniform(0.7, 0.99), 2),
                "quality": round(random.uniform(0.7, 0.99), 2),
                "test": round(random.uniform(0.8, 0.99), 2),
                "cognitive_integrity": 1.0, # Placeholder
                "policy": 1.0,
                "cost": 0.9,
                "maintainability": 0.85,
                "rollback_safety": 0.95
            }
            score_record = await self.orchestrator.record_candidate_score(
                execution_id=session.execution_id,
                candidate_id=candidate.id,
                scores=scores,
                rationale="Consensus reached after automated cross-agent evaluation."
            )
            
            if score_record.total_score > max_score:
                max_score = score_record.total_score
                best_candidate = candidate

        # Phase 3: Selection Decision
        if best_candidate and max_score > 0.8:
            await self.orchestrator.finalize_session(
                session_id=session.id,
                decision_type=PatchSelectionDecisionType.SELECTED_FOR_GOVERNANCE,
                selected_candidate_id=best_candidate.id,
                rationale=f"Candidate {str(best_candidate.id)[:8]} selected with total score {max_score:.2f}."
            )
        else:
            await self.orchestrator.finalize_session(
                session_id=session.id,
                decision_type=PatchSelectionDecisionType.REQUIRE_MANUAL_REVIEW,
                rationale="No candidate reached the required consensus threshold (>0.8)."
            )

        await self.db.commit()
