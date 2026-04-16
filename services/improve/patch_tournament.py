
"""
services/improve/patch_tournament.py — Phase 28
Coordinates the candidate generation, ranking, and final selection process.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from services.improve.models import RepairCandidate, TournamentResult, CandidateEvaluation
from services.improve.candidate_generator import CandidateGenerator
from services.improve.patch_ranker import PatchRanker
from services.improve.benchmark_loader import BenchmarkCase
from services.observability.logging import get_logger

from libs.llm.model_orchestrator import ModelOrchestrator

logger = get_logger("repair.tournament")

class PatchTournament:
    def __init__(self, model_orch: ModelOrchestrator, ranker: Optional[PatchRanker] = None):
        self.generator = CandidateGenerator(model_orch)
        self.ranker = ranker or PatchRanker()

    async def run_tournament(self, case: BenchmarkCase) -> TournamentResult:
        """Executes the full tournament for a given case."""
        started_at = datetime.now(timezone.utc)
        logger.info(f"[TOURNAMENT] Starting for case: {case.id}")

        # 1. Generate Candidates
        candidates = await self.generator.generate_candidates(case)
        
        # 2. Evaluate each candidate
        evaluations = []
        for c in candidates:
            eval_res = await self.ranker.evaluate_candidate(case, c)
            evaluations.append(eval_res)
            
        # 3. Select Winner
        qualified_evals = [e for e in evaluations if e.is_qualified]
        winner_eval = None
        winner_id = None
        rationale = "No qualified candidates found."

        if qualified_evals:
            winner_eval = max(qualified_evals, key=lambda x: x.scores.total_score)
            winner_id = winner_eval.candidate_id
            rationale = winner_eval.scores.justification

        completed_at = datetime.now(timezone.utc)
        
        result = TournamentResult(
            case_id=case.id,
            candidates=candidates,
            evaluations=evaluations,
            winner_id=winner_id,
            winning_rationale=rationale,
            started_at=started_at,
            completed_at=completed_at
        )

        logger.info(f"[TOURNAMENT] Winner for {case.id}: {winner_id} with score {winner_eval.scores.total_score:.2f} if winner_eval else 0")
        return result
