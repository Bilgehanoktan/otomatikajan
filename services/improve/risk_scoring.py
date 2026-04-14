"""
Improvement Risk Scoring Service
───────────────────────────────
Evaluates the safety of a proposed patch before rollout.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RiskScoring:
    @staticmethod
    def evaluate_patch(patch_diff: str, target_file: str, complexity_stats: Dict[str, Any] = None) -> float:
        """
        Returns a risk score between 0.0 (safe) and 1.0 (extremely risky).
        """
        score = 0.1 # Base risk
        
        # 1. Criticality of files
        critical_paths = ["libs/db", "libs/workflow", "services/auth"]
        if any(p in target_file for p in critical_paths):
            score += 0.4
            
        # 2. Size of change
        lines = patch_diff.split("\n")
        added = len([l for l in lines if l.startswith("+")])
        deleted = len([l for l in lines if l.startswith("-")])
        total_changes = added + deleted
        
        if total_changes > 100:
            score += 0.3
        elif total_changes > 20:
            score += 0.1
            
        # 3. Known sensitivity (conceptual)
        if "delete" in patch_diff.lower() or "drop" in patch_diff.lower():
            score += 0.2

        return min(score, 1.0)

    @staticmethod
    def get_approval_requirement(risk_score: float) -> str:
        """Determines if the patch can be auto-applied or needs human gate."""
        if risk_score < 0.2:
            return "auto" # Safe to canary
        elif risk_score < 0.5:
            return "manager_approval"
        else:
            return "admin_critical_verification"
