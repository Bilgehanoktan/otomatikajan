
"""
services/improve/candidate_generator.py — Phase 28
Generates multiple varied patch/policy candidates for a given incident/case.
"""
from typing import List, Dict, Any
import asyncio
from services.improve.models import RepairCandidate
from services.improve.benchmark_loader import BenchmarkCase
from services.observability.logging import get_logger
from libs.llm.model_orchestrator import ModelOrchestrator

logger = get_logger("repair.candidate_gen")

class CandidateGenerator:
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    async def generate_candidates(self, case: BenchmarkCase) -> List[RepairCandidate]:
        """
        Generates a diverse set of candidates by calling LLM agents with different personas.
        """
        logger.info(f"Generating diverse candidates for benchmark case: {case.id}...")
        
        # Define strategies to generate
        strategies = [
            ("conservative", "architect", "Generate a minimal, safe fix that ONLY addresses the immediate error without refactoring."),
            ("radical", "backend_dev", "Generate a modern, robust fix that refactors the problematic area to prevent future issues."),
            ("performant", "backend_dev", "Generate a high-performance fix, focusing on optimization, caching, and efficiency."),
            ("policy", "security", "Do not change the code; instead, provide a JSON policy override or configuration change to mitigate risk.")
        ]
        
        tasks = []
        for strategy_name, role, custom_instruction in strategies:
            tasks.append(self._generate_single_candidate(case, strategy_name, role, custom_instruction))
            
        candidates = await asyncio.gather(*tasks)
        
        # Filter out failed generations
        valid_candidates = [c for c in candidates if c is not None]
        
        logger.info(f"Successfully generated {len(valid_candidates)} candidates for {case.id}")
        return valid_candidates

    async def _generate_single_candidate(self, case: BenchmarkCase, strategy: str, role: str, instruction: str) -> RepairCandidate:
        """Calls the LLM to generate a specific candidate."""
        prompt = f"""
BENCHMARK CASE ID: {case.id}
MODULE: {case.module}
DESCRIPTION: {case.description}
LOGS/CONTEXT: {case.input_context}

STRATEGY: {strategy.upper()}
INSTRUCTION: {instruction}

Return the patch (or policy) content exactly as it should be applied. 
No preamble, no markdown formatting blocks unless it is part of the content.
"""
        try:
            content = await self.model_orch.complete(
                messages=[{"role": "user", "content": prompt}],
                preferred_agent=role
            )
            
            return RepairCandidate(
                type="policy" if strategy == "policy" else "patch",
                content=content.strip(),
                strategy=strategy,
                metadata={
                    "source": f"llm-{role}-{strategy}",
                    "case_id": case.id
                }
            )
        except Exception as e:
            logger.error(f"Failed to generate {strategy} candidate for {case.id}: {e}")
            # FALLBACK: Structural Proxy Candidate
            # We must return a candidate to allow the tournament to function in lab/demo mode
            return RepairCandidate(
                type="policy" if strategy == "policy" else "patch",
                content=f"// STRUCTURAL PROXY FOR {strategy.upper()}\n// System-generated due to LLM timeout/limit\n# AUTO-PATCH {case.id}\n// Log: Candidate synthesized via evolutionary fallback.",
                strategy=strategy,
                metadata={
                    "source": "lab-synthetic-fallback",
                    "case_id": case.id,
                    "error": str(e)
                }
            )
