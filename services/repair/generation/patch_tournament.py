import logging
from typing import List, Dict, Any, Tuple
from services.repair.generation.candidate_generator import RepairCandidate

logger = logging.getLogger("repair.generation.tournament")

class PatchTournament:
    """Ranks and selects the optimal repair candidate using a Unified Scorer + Verifier Mesh."""
    
    def __init__(self, risk_weight: float = 0.3, cost_weight: float = 0.2, verifier_weight: float = 0.5):
        self.risk_weight = risk_weight
        self.cost_weight = cost_weight
        self.verifier_weight = verifier_weight
        
    async def run_tournament(
        self, 
        candidates: List[RepairCandidate], 
        verifiers: List[Any], 
        context: Dict[str, Any]
    ) -> Tuple[RepairCandidate, float]:
        """Arbitrates between candidates by running them through the Verifier Mesh."""
        if not candidates:
            raise ValueError("Tournament requires at least one candidate.")
            
        logger.info(f"Starting Multi-Candidate Tournament with {len(candidates)} entries.")
        
        scored_candidates = []
        for c in candidates:
            # 1. Verification Score calculation
            verifier_score = 0.0
            total_verifiers = len(verifiers)
            
            for verifier in verifiers:
                try:
                    passed = await verifier.verify(c.patch_payload, context)
                    if passed:
                        verifier_score += (1.0 / total_verifiers)
                except Exception as e:
                    logger.error(f"Verifier {verifier.__class__.__name__} failed for candidate {c.id}: {e}")
            
            # 2. Unified Scoring Logic (Higher is Better)
            risk_part = (1.0 - c.risk_score) * self.risk_weight
            cost_normal = max(0, 1.0 - (c.estimated_cost / 1000.0))
            cost_part = cost_normal * self.cost_weight
            verifier_part = verifier_score * self.verifier_weight
            
            unified_score = round(risk_part + cost_part + verifier_part, 4)
            scored_candidates.append((c, unified_score))
            
            logger.info(f"Candidate '{c.strategy_name}' -> Verifier Score: {verifier_score:.2f} | Unified: {unified_score}")
            
        # 3. Selection
        winner, winning_score = max(scored_candidates, key=lambda x: x[1])
        
        logger.info(f"Tournament Winner: {winner.strategy_name} with score {winning_score}")
        return winner, winning_score
