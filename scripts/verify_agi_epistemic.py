import asyncio
import os
import sys

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_epistemic_and_strategy():
    print("--- AGI 12.6 & 12.7 Verification ---")
    
    try:
        from core.agi.cognitive.perception_gate import perception_gate
        from core.agi.adaptation.strategy_tuner import strategy_tuner
        from core.agi.orchestrator import agi_orchestrator
        from core.agi.schemas import ProblemFrame, TaskType, RiskLevel
        
        print("[OK] AGI 12.6/12.7 components imported successfully.")
        
        # Test Strategy Tuner
        frame = ProblemFrame(task_type=TaskType.FIX, objective="Critical Fix", risk_level=RiskLevel.CRITICAL)
        strategy = await strategy_tuner.determine_strategy([], frame)
        print(f"[OK] Strategy Tuner: {strategy.max_attempts} attempts, Simulation: {strategy.simulation_required}")
        
        # Test Perception Gate Presence
        print(f"[OK] Perception Gate ready for probing.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_epistemic_and_strategy())
