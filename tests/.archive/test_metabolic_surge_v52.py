import asyncio
import logging
import os
import sys
import time

# Project root to sys.path
sys.path.append(os.getcwd())

from packages.llm_gateway.model_orchestrator import PROVIDERS, ProviderStats, CircuitState, LLMResponse
from packages.orchestration.agi.operational.metabolic_governor import metabolic_governor

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("test_v52")

async def test_metabolic_routing():
    _log.info("Testing Sovereign Metabolism (Phase 52)...")
    
    # Mock provider map
    # 1. OpenAI (Fast but failing)
    p1 = ProviderStats(name="openai", api_key_env="MOCK", base_url="MOCK", model="MOCK")
    p1.circuit = CircuitState.OPEN
    p1.quarantine_until = time.time() + 100
    
    # 2. Gemini (Slow but healthy)
    p2 = ProviderStats(name="gemini", api_key_env="MOCK", base_url="MOCK", model="MOCK")
    p2.record_success(latency=0.5)
    p2.success = 10
    p2.total_latency = 5.0 # avg 0.5s
    
    # 3. Groq (Very fast and healthy)
    p3 = ProviderStats(name="groq", api_key_env="MOCK", base_url="MOCK", model="MOCK")
    p3.record_success(latency=0.1)
    p3.success = 20
    p3.total_latency = 2.0 # avg 0.1s
    
    provider_map = {"openai": p1, "gemini": p2, "groq": p3}
    
    _log.info("Triggering metabolic selection...")
    candidates = ["openai", "gemini", "groq"]
    
    # OpenAI is quarantined, gemini has 0.5s latency, groq has 0.1s.
    # Groq should be chosen first.
    best = metabolic_governor.get_optimal_provider(candidates, provider_map)
    _log.info(f"Optimal provider selected: {best}")
    
    assert best == "groq", f"Groq should be best, got {best}"
    _log.info("✅ Metabolic Routing selected the fastest/healthiest model.")

async def test_metabolic_governance_stress():
    _log.info("Testing Metabolic Governance Stress Analysis...")
    
    # Mocking a high-stress scenario (most providers failing)
    p1 = ProviderStats(name="p1", api_key_env="MOCK", base_url="MOCK", model="MOCK")
    p1.circuit = CircuitState.OPEN
    p2 = ProviderStats(name="p2", api_key_env="MOCK", base_url="MOCK", model="MOCK")
    p2.circuit = CircuitState.OPEN
    
    provider_map = {"p1": p1, "p2": p2}
    
    # Stress check
    # Force interval bypass by resetting _last_check
    metabolic_governor._last_check = 0
    await metabolic_governor.update_metabolism(provider_map)
    
    _log.info("✅ Metabolic stress check passed.")

if __name__ == "__main__":
    asyncio.run(test_metabolic_routing())
    asyncio.run(test_metabolic_governance_stress())
