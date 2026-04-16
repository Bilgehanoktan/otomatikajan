import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger("repair.generation.candidates")

class RepairCandidate(BaseModel):
    """A proposed repair strategy waiting for tournament entry."""
    id: str = Field(default_factory=lambda: f"cand_{uuid.uuid4().hex[:8]}")
    strategy_name: str
    patch_payload: Dict[str, Any]
    risk_score: float = 0.5
    estimated_cost: float = 0.0
    confidence: float = 0.0
    reasoning: str = ""

class CandidateGenerator:
    """Generates a diverse set of repair candidates for a given incident."""
    
    def __init__(self, model_orch=None):
        self.model_orch = model_orch

    async def generate_variants(self, incident_type: str, payload: Dict[str, Any]) -> List[RepairCandidate]:
        """Produces 3-5 distinct candidates with varying trade-offs using LLM guidance."""
        """Produces 3 distinct candidates with varying trade-offs using LLM."""
        if not self.model_orch:
            logger.warning("No model_orchestrator provided, falling back to mock candidates.")
            return self._get_mock_candidates(incident_type, payload)

        logger.info(f"Generating real multi-candidate strategies for: {incident_type}")
        
        system_prompt = """You are the Sovereign AGI Repair Intelligence. 
Your goal is to generate 3 distinct repair strategies for the given incident.
Vary the strategies by:
1. Conservative (Safety-First, low risk, low cost)
2. Moderate (Standard fix, medium risk, balanced cost)
3. Aggressive (High-performance recovery, higher risk/cost)

Return ONLY a JSON list of objects matching the RepairCandidate schema:
{
  "id": "unique_string",
  "strategy_name": "Human_Readable_Name",
  "patch_payload": {}, 
  "risk_score": 0.0 to 1.0,
  "estimated_cost": numeric,
  "confidence": 0.0 to 1.0,
  "reasoning": "Quick explanation"
}"""

        user_prompt = f"Incident Type: {incident_type}\nPayload: {payload}\nGenerate 3 variants."

        try:
            response = await self.model_orch.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                preferred_agent="backend_dev",
                temperature=0.4
            )
            
            # Basic parsing - in production we'd use a more robust JSON extractor
            import json
            import re
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                raw_list = json.loads(json_match.group(0))
                return [RepairCandidate(**c) for c in raw_list]
            
        except Exception as e:
            logger.error(f"LLM Candidate Generation failed: {e}")
        
        return self._get_mock_candidates(incident_type, payload)

    def _get_mock_candidates(self, incident_type: str, payload: Dict[str, Any]) -> List[RepairCandidate]:
        """Fallback mock candidates."""
        return [
            RepairCandidate(
                id="cand_cons",
                strategy_name="Conservative_Stability",
                patch_payload={"action": "throttle", "limit": "50%"},
                risk_score=0.1,
                estimated_cost=5.0,
                confidence=0.95,
                reasoning="Safety-first mock fallback."
            ),
            RepairCandidate(
                id="cand_mod",
                strategy_name="Moderate_Structural",
                patch_payload={"action": "rebalance"},
                risk_score=0.4,
                estimated_cost=25.0,
                confidence=0.85,
                reasoning="Balanced mock fallback."
            )
        ]

    def _generate_economic_candidates(self, payload: Dict[str, Any]) -> List[RepairCandidate]:
        return [
            RepairCandidate(
                strategy_name="Cost_Cap_Enforce",
                patch_payload={"action": "kill_waste", "threshold": 0.8},
                risk_score=0.2, estimated_cost=0.0, confidence=0.9,
                reasoning="Strict enforcement of financial caps."
            ),
            RepairCandidate(
                strategy_name="Elastic_Quota_Shift",
                patch_payload={"action": "reallocate", "source": "dev", "target": "prod"},
                risk_score=0.3, estimated_cost=10.0, confidence=0.8,
                reasoning="Moving existing budget without increasing total spend."
            ),
            RepairCandidate(
                strategy_name="Tier_Upgrade_ROI",
                patch_payload={"action": "upgrade_tier", "reason": "efficiency_gain"},
                risk_score=0.5, estimated_cost=200.0, confidence=0.7,
                reasoning="Spending more now to increase efficiency and lower long-term MTBF."
            )
        ]

    def _generate_performance_candidates(self, payload: Dict[str, Any]) -> List[RepairCandidate]:
        return [
            RepairCandidate(
                strategy_name="Cache_Invalidation",
                patch_payload={"action": "clear_cache", "scope": "region"},
                risk_score=0.2, estimated_cost=1.0, confidence=0.9,
                reasoning="Quick fix for staleness but might cause temporary latency spikes."
            ),
            RepairCandidate(
                strategy_name="Horizontal_AutoScaling",
                patch_payload={"action": "add_replicas", "count": 2},
                risk_score=0.3, estimated_cost=50.0, confidence=0.85,
                reasoning="Classic scaling approach to handle pressure."
            ),
            RepairCandidate(
                strategy_name="Kernel_Parameter_Tuning",
                patch_payload={"action": "tune_tcp_buffers", "mode": "aggressive"},
                risk_score=0.6, estimated_cost=0.0, confidence=0.6,
                reasoning="Deep tuning that carries high risk but maximizes specific throughput."
            )
        ]
