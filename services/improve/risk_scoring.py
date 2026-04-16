"""
Improvement Risk Scoring Service
───────────────────────────────
Evaluates the safety of a proposed patch before rollout.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RiskScoring:
    CRITICAL_PATHS = ["libs/db", "libs/workflow", "services/auth", "libs/vcs"]
    ROLLBACK_SENSITIVE_KEYWORDS = ["migration", "drop table", "truncate", "alembic"]

    @staticmethod
    def evaluate_path_and_instruction(target_file: str, instruction: str) -> Dict[str, Any]:
        """
        Evaluates risk BEFORE patch generation based on target path and intent.
        """
        factors = []
        score = 0.1
        
        # 1. Path Criticality
        if any(p in target_file for p in RiskScoring.CRITICAL_PATHS):
            score += 0.4
            factors.append("Kritik sistem yolu (core path)")

        # 2. Instruction Intent Analysis
        danger_keywords = ["delete", "drop", "overwrite", "auth", "encrypt", "credential"]
        if any(k in instruction.lower() for k in danger_keywords):
            score += 0.3
            factors.append("Yüksek riskli anahtar kelimeler tespit edildi")

        final_score = min(score, 1.0)
        return {
            "score": final_score,
            "factors": factors
        }

    @staticmethod
    def evaluate_patch(patch_diff: str, target_file: str, complexity_stats: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Returns a detailed risk evaluation.
        """
        factors = []
        score = 0.1 # Base risk
        
        # 1. Path Criticality
        if any(p in target_file for p in RiskScoring.CRITICAL_PATHS):
            score += 0.4
            factors.append("Critical system path detected")
            
        # 2. Change Magnitude
        lines = patch_diff.split("\n")
        added = len([l for l in lines if l.startswith("+")])
        deleted = len([l for l in lines if l.startswith("-")])
        total_changes = added + deleted
        
        if total_changes > 100:
            score += 0.3
            factors.append("Large change scope (>100 lines)")
        elif total_changes > 20:
            score += 0.1
            factors.append("Moderate change scope")
            
        # 3. Rollability (Conceptual)
        if any(k in patch_diff.lower() for k in RiskScoring.ROLLBACK_SENSITIVE_KEYWORDS):
            score += 0.3
            factors.append("Potentially irreversible side-effects detected (migrations)")

        # 4. Scope / Dependency Factor (Placeholder)
        # In a real system, we'd check how many files import 'target_file'
        
        final_score = min(score, 1.0)
        
        return {
            "score": final_score,
            "level": "low" if final_score < 0.2 else "medium" if final_score < 0.5 else "high",
            "factors": factors,
            "approval_required": RiskScoring.get_approval_requirement(final_score)
        }

    @staticmethod
    def get_approval_requirement(risk_score: float) -> str:
        """Determines if the patch can be auto-applied or needs human gate."""
        if risk_score < 0.25:
            return "auto_canary" # Safe for auto-pilot
        elif risk_score < 0.6:
            return "operator_approval"
        else:
            return "admin_security_gate"
