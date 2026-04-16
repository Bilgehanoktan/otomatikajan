import logging
from typing import List, Dict, Any, Tuple
from services.repair.generation.candidate_generator import RepairCandidate

logger = logging.getLogger("repair.generation.tournament")

class PatchTournament:
    """Ranks and selects the optimal repair candidate using a Unified Scorer."""
    
    def __init__(self, risk_weight: float = 0.4, cost_weight: float = 0.2, confidence_weight: float = 0.4):
        self.risk_weight = risk_weight
        self.cost_weight = cost_weight
        self.confidence_weight = confidence_weight

    def score_candidate(self, candidate: RepairCandidate) -> float:
        """Calculates the unified score for a candidate (Higher is Better)."""
        # Risk is negative (we want low risk)
        risk_part = (1.0 - candidate.risk_score) * self.risk_weight
        
        # Cost is negative (we want low cost, but we normalize it loosely)
        # Assuming max cost seen is 1000 for normalization
        cost_normal = max(0, 1.0 - (candidate.estimated_cost / 1000.0))
        cost_part = cost_normal * self.cost_weight
        
        confidence_part = candidate.confidence * self.confidence_weight
        
        unified_score = risk_part + cost_part + confidence_part
        return round(unified_score, 4)

    async def run_tournament(self, candidates: List[RepairCandidate]) -> Tuple[RepairCandidate, float]:
        """Arbitrates between candidates and returns the winner with its score."""
        if not candidates:
            raise ValueError("Tournament requires at least one candidate.")
            
        logger.info(f"Starting Patch Tournament with {len(candidates)} candidates.")
        
        scored_candidates = []
        for c in candidates:
            score = self.score_candidate(c)
            scored_candidates.append((c, score))
            logger.info(f"Tournament Entry: {c.strategy_name} | Score: {score}")
            
        # Rank by score descending
        winner, winning_score = max(scored_candidates, key=lambda x: x[1])
        
        logger.info(f"Tournament Winner: {winner.strategy_name} ({winning_score})")
        return winner, winning_score
