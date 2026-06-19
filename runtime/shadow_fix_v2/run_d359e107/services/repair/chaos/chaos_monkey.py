"""
Sovereign AGI — Phase 19 (L5 Autonomy)
services/repair/chaos/chaos_monkey.py
Fault Injection Engine. Introduces deliberate faults (latency, disconnections) 
to train and evaluate the SelfHealEngine in a controlled manner.
"""

import random
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ChaosMonkey:
    """
    Randomly injects faults to ensure SelfHealEngine's prompt responses and recovery 
    strategies are actually working before a real incident occurs.
    """
    def __init__(self, probability: float = 0.05, active: bool = False):
        self.probability = probability
        self.active = active
        self.chaos_events_triggered = 0

    def enable(self):
        self.active = True
        logger.warning("[CHAOS] Chaos Monkey ENABLED.")

    def disable(self):
        self.active = False
        logger.info("[CHAOS] Chaos Monkey DISABLED.")

    async def intercept_request(self, agent_id: str) -> Optional[Exception]:
        """
        To be called inside the Orhestrator or SubTask execution wrapper.
        If it returns an Exception, the wrapper should raise it.
        """
        if not self.active:
            return None

        if random.random() > self.probability:
            return None

        self.chaos_events_triggered += 1
        fault_type = random.choice([
            "latency",
            "db_disconnect",
            "llm_timeout",
            "internal_error"
        ])

        logger.critical(f"[CHAOS MONKEY] Injecting {fault_type} on agent {agent_id}")

        if fault_type == "latency":
            # Just hang for 30s to trigger Timeout Strategy
            await asyncio.sleep(30)
            return TimeoutError(f"Chaos Monkey injected 30s latency on {agent_id}")
            
        elif fault_type == "db_disconnect":
            return ConnectionError(f"Chaos Monkey simulated DB connection drop on {agent_id}")
            
        elif fault_type == "llm_timeout":
            # Simulate Provider Rate Limit or Crash
            from tenacity import RetryError
            return Exception(f"RateLimitError: Chaos Monkey simulated 429 Too Many Requests")
            
        elif fault_type == "internal_error":
            return ValueError(f"Chaos Monkey simulated a rogue ValueError in {agent_id}'s parser.")

        return None

# Singleton to be imported globally or injected
chaos_monkey = ChaosMonkey()
