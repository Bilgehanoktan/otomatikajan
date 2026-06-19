
"""
services/improve/patch_ranker.py — Phase 28
Scores and ranks repair candidates based on the Verifier Mesh output.
"""
import random
from typing import List, Dict, Any
from services.improve.models import RepairCandidate, CandidateScore, CandidateEvaluation
from services.improve.benchmark_loader import BenchmarkCase
from services.observability.logging import get_logger

logger = get_logger("repair.ranker")

class PatchRanker:
    def __init__(self):
        # Default weights (Phase 28 calibration baselines)
        self.weights = {
            "syntax": 0.2,
            "regression": 0.3,
            "policy": 0.15,
            "risk": 0.15,
            "economic": 0.1,
            "similarity": 0.1
        }

    async def _load_calibrated_weights(self):
        """Loads approved self-tuning suggestions to override defaults."""
        from libs.db.session import session_scope
        from libs.db.models.repair_models import SelfTuningSuggestion
        from sqlalchemy import select
        
        try:
            async with session_scope() as session:
                # Fetch approved weight adjustments
                stmt = select(SelfTuningSuggestion).where(SelfTuningSuggestion.status == "approved")
                result = await session.execute(stmt)
                approved = result.scalars().all()
                
                for suggestion in approved:
                    if suggestion.parameter_name in self.weights:
                        self.weights[suggestion.parameter_name] = suggestion.proposed_value
                        logger.info(f"[TUNING] Applied calibrated weight: {suggestion.parameter_name} = {suggestion.proposed_value}")
        except Exception as e:
            logger.error(f"Failed to load calibrated weights: {e}")

    async def evaluate_candidate(self, case: BenchmarkCase, candidate: RepairCandidate) -> CandidateEvaluation:
        """
        Runs the full Verifier Mesh on a candidate.
        """
        await self._load_calibrated_weights()
        
        from services.improve.verifier_mesh import VerifierMesh
        mesh = VerifierMesh()
        
        evaluation = await mesh.verify_candidate(case, candidate)
        
        # --- PHASE 28 Workstream D: Learning Boost/Penalty ---
        from services.improve.repair_memory import RepairMemory
        memory = RepairMemory()
        pattern = memory.get_pattern_for_strategy(candidate.strategy, case.module)
        
        memory_multiplier = 1.0
        if pattern.recommendation == "penalize":
            memory_multiplier = 0.5
            logger.warning(f"[LEARNING] Penalizing strategy {candidate.strategy} (History Fail Rate: {1-pattern.avg_success_rate:.2f})")
        elif pattern.recommendation == "boost":
            memory_multiplier = 1.2
            logger.info(f"[LEARNING] Boosting strategy {candidate.strategy} (History Success Rate: {pattern.avg_success_rate:.2f})")

        # Apply weights and memory multiplier
        s = evaluation.scores
        s.similarity_score = pattern.avg_success_rate # Use success rate as similarity/historical score
        
        s.total_score = (
            s.syntax_score * self.weights["syntax"] +
            s.regression_score * self.weights["regression"] +
            s.policy_score * self.weights["policy"] +
            s.risk_score * self.weights["risk"] +
            s.economic_score * self.weights["economic"] +
            s.similarity_score * self.weights["similarity"]
        ) * memory_multiplier
        
        return evaluation
