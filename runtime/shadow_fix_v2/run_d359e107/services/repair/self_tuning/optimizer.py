import logging
import asyncio
from typing import Dict, Any, List
from services.repair.repair_memory import RepairMemory, RepairOutcome

_log = logging.getLogger("repair.self_tuning")

class WeightOptimizer:
    """
    Self-tuning engine that adjusts tournament weights based on evidence.
    Implements Phase 28 Stage 3: Evidence-Driven Calibration.
    """
    
    def __init__(self, memory: RepairMemory):
        self.memory = memory
        self.default_weights = {
            "risk_weight": 0.4,
            "cost_weight": 0.2,
            "verifier_weight": 0.4
        }
    
    async def calculate_optimal_weights(self) -> Dict[str, float]:
        """Analyzes historical outcomes to optimize tournament arbitration."""
        _log.info("Starting Weight Optimization Cycle based on Learning Fabric [PEL-SIF-02].")
        
        try:
            # 1. Fetch Global Learning Stats (Phase 31 integration)
            from services.governance.learning_orchestrator import LearningOrchestrator
            stats = await LearningOrchestrator.get_global_learning_stats()
            
            success_rate = stats.get("success_rate", 1.0)
            rollbacks = stats.get("total_rollbacks", 0)
            rejects = stats.get("total_rejects", 0)
            
            new_weights = self.default_weights.copy()
            
            # 2. Logic: If system is performing well, favor efficiency (cost)
            if success_rate > 0.9 and rollbacks == 0 and rejects == 0:
                _log.info("System is stable. Shifting bias toward Efficiency (Cost).")
                new_weights["risk_weight"] = 0.3
                new_weights["cost_weight"] = 0.3
                new_weights["verifier_weight"] = 0.4
            
            # 3. Logic: If system has high failure or rollbacks, harden the gates
            elif success_rate < 0.7 or rollbacks > 2 or rejects > 3:
                _log.warning(f"Instability detected (Success: {success_rate:.2f}, Rollbacks: {rollbacks}). Hardening Risk and Verification.")
                new_weights["risk_weight"] = 0.5
                new_weights["cost_weight"] = 0.1
                new_weights["verifier_weight"] = 0.4
            
            # 4. Logic: If many operator rejects, increase human review importance (Risk)
            if rejects > 5:
                _log.warning("High operator rejection rate. Increasing Risk sensitivity.")
                new_weights["risk_weight"] += 0.1
                new_weights["verifier_weight"] -= 0.1

            return new_weights
        except Exception as e:
            _log.error(f"Weight optimization failed: {e}")
            return self.default_weights

class TrendAnalyzer:
    """Analyzes repair patterns across modules to identify problematic components."""
    
    async def analyze_top_offenders(self, memory: RepairMemory) -> List[str]:
        # This would identify components with high failure rates or high costs
        return ["RedisProxy"] # Mocked for Phase 28
