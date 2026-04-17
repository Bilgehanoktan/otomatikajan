
import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from services.improve.evolution_orchestrator import init_evolution_orchestrator
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

logger = get_logger("test.evolution")

async def test_evolution():
    logger.info("Starting Evolution Orchestrator Test...")
    model_orch = ModelOrchestrator()
    project_root = os.getcwd()
    
    orchestrator = init_evolution_orchestrator(model_orch, project_root)
    
    # 1. Test TODO Scan
    todos = orchestrator._scan_for_todos()
    logger.info(f"Found {len(todos)} files with TODOs.")
    
    # 2. Test Plan Generation (Dry Run - don't apply)
    plan = await orchestrator._generate_evolution_plan()
    if plan:
        logger.info(f"Generated Plan: {plan['target_file']} -> {plan['instruction']}")
    else:
        logger.error("Failed to generate plan.")

if __name__ == "__main__":
    asyncio.run(test_evolution())
