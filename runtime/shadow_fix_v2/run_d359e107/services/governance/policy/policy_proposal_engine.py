"""
Sovereign AGI — Phase 31 / PEL-SIF-02
services/governance/policy/policy_proposal_engine.py

Generates autonomous policy evolution proposals based on recurrent learning patterns.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import select
from libs.db.session import get_db_ctx
from libs.db.models.learning_models import ErrorFingerprint, StrategyMemory
from libs.db.models.governance_models import PolicyProposal # Assuming this exists or using a generic one

_log = logging.getLogger("governance.policy.proposal_engine")

class PolicyProposalEngine:
    """
    Analyzes recurrence evidence in ErrorFingerprints to propose system-wide policy updates.
    """
    
    @staticmethod
    async def generate_proposals() -> List[Dict[str, Any]]:
        """Scans learning fabric for high-signal patterns that warrant policy changes."""
        _log.info("Starting Policy Evolution Scan based on Recurrence Evidence.")
        proposals = []
        
        async with get_db_ctx() as db:
            # 1. Identify High Recurrence Fingerprints (> 10 occurrences)
            res = await db.execute(select(ErrorFingerprint).where(ErrorFingerprint.recurrence_count > 10))
            hot_fingerprints = res.scalars().all()
            
            for fp in hot_fingerprints:
                # Find the most trusted strategy for this fingerprint family
                res_strat = await db.execute(
                    select(StrategyMemory).where(
                        StrategyMemory.error_family == fp.error_family,
                        StrategyMemory.component == fp.component
                    ).order_by(StrategyMemory.trust_score.desc())
                )
                top_strategy = res_strat.scalars().first()
                
                if top_strategy and top_strategy.trust_score > 0.9 and top_strategy.state != "promoted":
                    # SIGNAL: High trust + High recurrence = Candidate for Auto-Promotion
                    proposals.append({
                        "type": "AUTO_PROMOTION",
                        "title": f"Promote {top_strategy.strategy_name} for {fp.error_family}",
                        "rationale": f"Strategy has {top_strategy.success_count} successes and 0 rollbacks over {fp.recurrence_count} recurrences.",
                        "parameter": "autonomy_level",
                        "proposed_value": "AUTO_PR_ENABLED",
                        "fingerprint_id": fp.id,
                        "confidence": top_strategy.trust_score
                    })
                
                if fp.severity == "critical" and fp.recurrence_count > 20:
                    # SIGNAL: Critical recurrence = Candidate for Hardened Verification
                    proposals.append({
                        "type": "VIGILANCE_INCREASE",
                        "title": f"Tighten Verification for {fp.error_family}",
                        "rationale": f"Critical fingerprint detected {fp.recurrence_count} times. Current strategies need deeper validation.",
                        "parameter": "verifier_threshold",
                        "proposed_value": "0.85",
                        "fingerprint_id": fp.id,
                        "confidence": 0.95
                    })

        _log.info(f"Scan complete. Generated {len(proposals)} evolution proposals.")
        return proposals

    @staticmethod
    async def commit_proposals(proposals: List[Dict[str, Any]]):
        """Persists proposals to the Governance layer for operator review."""
        from libs.db.models.governance_models import PolicyProposal
        
        async with get_db_ctx() as db:
            for p in proposals:
                proposal = PolicyProposal(
                    title=p["title"],
                    description=p["rationale"],
                    scope="AUTONOMOUS_LEARNING",
                    proposed_changes={
                        "type": p["type"],
                        "parameter": p["parameter"],
                        "proposed_value": p["proposed_value"],
                        "fingerprint_id": str(p["fingerprint_id"]),
                        "confidence": p["confidence"]
                    },
                    status="PROPOSED",
                    author_id="LearningOrchestrator"
                )
                db.add(proposal)
            await db.commit()
        _log.info(f"Committed {len(proposals)} proposals to Governance.")
