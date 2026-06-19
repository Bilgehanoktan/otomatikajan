import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIPatchNegotiationSession, UIPatchDebateTurn, UIPatchCandidate, 
    PatchNegotiationStatus, PatchDebateTurnType, UIPatchSelectionDecision,
    PatchSelectionDecisionType, UIPatchCandidateScore
)
from services.ui_repair.war_room_evidence_writer import WarRoomEvidenceWriter

class PatchNegotiationOrchestrator:
    """
    Phase 28: Orchestrates multi-agent patch negotiation and consensus building.
    Allows different agents (Stagehand, OpenSWE, Verifier) to debate and score patches.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence = WarRoomEvidenceWriter(db)

    async def start_session(self, execution_id: uuid.UUID, agent_names: List[str]) -> UIPatchNegotiationSession:
        result = await self.db.execute(select(UIPatchCandidate).where(UIPatchCandidate.execution_id == execution_id))
        candidates = result.scalars().all()
        
        session = UIPatchNegotiationSession(
            execution_id=execution_id,
            status=PatchNegotiationStatus.RUNNING,
            participant_agents_json={"agents": agent_names},
            candidate_count=len(list(candidates)),
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # Initial proposal turn
        for agent in agent_names:
            await self.add_debate_turn(
                session.id, 
                agent, 
                PatchDebateTurnType.PROPOSAL, 
                f"Agent {agent} joined the negotiation for {len(list(candidates))} candidates."
            )
            
        return session

    async def add_debate_turn(self, session_id: uuid.UUID, agent_name: str, 
                        turn_type: PatchDebateTurnType, message: str, 
                        candidate_id: Optional[uuid.UUID] = None,
                        claims: Optional[Dict[str, Any]] = None,
                        evidence_refs: Optional[Dict[str, Any]] = None) -> UIPatchDebateTurn:
        turn = UIPatchDebateTurn(
            negotiation_session_id=session_id,
            agent_name=agent_name,
            candidate_id=candidate_id,
            turn_type=turn_type,
            message=message,
            claims_json=claims or {},
            evidence_refs_json=evidence_refs or {}
        )
        self.db.add(turn)
        await self.db.commit()
        await self.db.refresh(turn)
        return turn

    async def record_candidate_score(self, execution_id: uuid.UUID, candidate_id: uuid.UUID, scores: Dict[str, float], rationale: str):
        score_record = UIPatchCandidateScore(
            execution_id=execution_id,
            candidate_id=candidate_id,
            safety_score=scores.get("safety", 0.0),
            quality_score=scores.get("quality", 0.0),
            test_score=scores.get("test", 0.0),
            cognitive_integrity_score=scores.get("cognitive_integrity", 0.0),
            policy_score=scores.get("policy", 0.0),
            cost_score=scores.get("cost", 0.0),
            maintainability_score=scores.get("maintainability", 0.0),
            rollback_safety_score=scores.get("rollback_safety", 0.0),
            total_score=sum(scores.values()) / len(scores) if scores else 0.0,
            scoring_rationale=rationale
        )
        self.db.add(score_record)
        await self.db.commit()
        return score_record

    async def finalize_session(self, session_id: uuid.UUID, decision_type: PatchSelectionDecisionType, 
                         selected_candidate_id: Optional[uuid.UUID] = None, rationale: str = ""):
        result = await self.db.execute(select(UIPatchNegotiationSession).where(UIPatchNegotiationSession.id == session_id))
        session = result.scalars().first()
        if not session:
            return

        session.status = PatchNegotiationStatus.CONSENSUS_REACHED if selected_candidate_id else PatchNegotiationStatus.DISAGREEMENT
        session.finished_at = datetime.now(timezone.utc)
        session.selected_candidate_id = selected_candidate_id
        session.final_rationale = rationale
        
        decision_val = decision_type.value if hasattr(decision_type, 'value') else decision_type
        decision = UIPatchSelectionDecision(
            execution_id=session.execution_id,
            negotiation_session_id=session.id,
            selected_candidate_id=selected_candidate_id,
            decision=decision_type,
            reason=rationale,
            operator_visible_explanation=f"Decision: {decision_val}. {rationale}"
        )
        self.db.add(decision)
        
        # Write evidence
        evidence_hash = self.evidence.write_execution_event(
            session.execution_id,
            "negotiation_finalized",
            f"Negotiation finalized with decision: {decision_val}"
        )
        session.evidence_hash = evidence_hash
        decision.evidence_hash = evidence_hash
        
        await self.db.commit()
        return decision
