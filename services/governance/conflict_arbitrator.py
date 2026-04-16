"""
Sovereign AGI — Phase 19
services/governance/conflict_arbitrator.py
The Arbitrator - Resolves conflicting proposals from different agent clusters.
"""
from __future__ import annotations
import yaml
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Proposal(BaseModel):
    proposal_id: str
    cluster_id: str
    target_resource: str
    action_type: str
    risk_score: float
    confidence_score: float
    priority: int

class ArbitrationResult(BaseModel):
    winning_proposal_id: str
    reason: str
    escalate_to_hitl: bool = False

class ConflictArbitrator:
    def __init__(self, policy_path: str = "configs/federation_policy.yaml"):
        self.policy_path = policy_path
        self.policy = self._load_policy()

    def _load_policy(self) -> Dict[str, Any]:
        if not os.path.exists(self.policy_path):
            return {}
        with open(self.policy_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    async def resolve_conflict(self, proposals: List[Proposal]) -> ArbitrationResult:
        """
        Arbitrates between multiple conflicting proposals.
        Logic: Priority > Risk Score > Confidence Score.
        """
        if not proposals:
            raise ValueError("No proposals provided for arbitration.")
        
        if len(proposals) == 1:
            return ArbitrationResult(winning_proposal_id=proposals[0].proposal_id, reason="No conflict: single candidate.")

        # 1. Sort by Priority (Descending)
        # 2. Sort by Risk Score (Ascending - Lower is safer)
        # 3. Sort by Confidence Score (Descending)
        
        # Priority mapping from policy precedence if not explicit in proposal
        # (Simplified: assume priority is already in Proposal from cluster config)
        
        sorted_proposals = sorted(
            proposals, 
            key=lambda p: (p.priority, -p.risk_score, p.confidence_score), 
            reverse=True
        )

        winner = sorted_proposals[0]
        runner_up = sorted_proposals[1]

        # 4. Check for Parity (Escalation Rule)
        margin = self.policy.get("arbitration_rules", {}).get("conflict_thresholds", {}).get("confidence_parity_margin", 0.05)
        
        # If priorities are same and risk/confidence are very close, escalate
        if winner.priority == runner_up.priority:
             risk_diff = abs(winner.risk_score - runner_up.risk_score)
             if risk_diff < margin:
                 return ArbitrationResult(
                     winning_proposal_id=winner.proposal_id, 
                     reason=f"Tie detected (Risk diff {risk_diff:.4f} < {margin}). Escalating to Human Expert.",
                     escalate_to_hitl=True
                 )

        return ArbitrationResult(
            winning_proposal_id=winner.proposal_id,
            reason=f"Resolved via Priority/Risk. Winner: {winner.cluster_id} override."
        )
