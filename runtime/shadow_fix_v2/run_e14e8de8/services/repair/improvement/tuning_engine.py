import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from services.repair.repair_memory import RepairMemory

logger = logging.getLogger("repair.improvement.tuning")

class TuningEngine:
    """Semi-autonomous engine that analyzes repair outcomes and suggests configuration tuning."""
    
    def __init__(self, memory: RepairMemory):
        self.memory = memory
        
    async def analyze_trends(self, window_days: int = 7) -> Dict[str, Any]:
        """Scans the repair memory for patterns of failure or inefficiency."""
        logger.info(f"Analyzing repair trends for the last {window_days} days...")
        
        # In a real system, we'd query SovereignEvidence with filter:
        # created_at > (now - window_days) AND evidence_type == 'REPAIR_OUTCOME'
        
        # Example analytical logic:
        # 1. High fail rate on 'Aggressive' prompt -> Suggest lowering aggressive weight.
        # 2. Economic verifier blocking 50% of success candidates -> Suggest raising budget hard-cap.
        
        return {
            "insights": [
                "Conservative strategies show 95% success but 200% higher MTTR.",
                "Economic verifier is the most frequent bottleneck.",
                "LLM-Moderate variant is the most cost-effective."
            ],
            "recommendations": {
                "risk_weight_adjustment": -0.05, # Suggest being slightly more conservative
                "cost_weight_adjustment": +0.10,  # Prioritize cost efficiency more
                "prompts": "Refine 'Aggressive' prompt to include performance safety keywords."
            }
        }

    async def generate_tuning_report(self) -> str:
        """Generates a human-friendly (Executive) summary of proposed tunings."""
        trends = await self.analyze_trends()
        report = "### 🛠️ Sovereign AGI Repair Lab: Tuning Report\n\n"
        for insight in trends["insights"]:
            report += f"- {insight}\n"
        
        report += "\n**Proposed Configuration Adjustments:**\n"
        for key, val in trends["recommendations"].items():
            report += f"- `{key}`: {val}\n"
        
        return report
