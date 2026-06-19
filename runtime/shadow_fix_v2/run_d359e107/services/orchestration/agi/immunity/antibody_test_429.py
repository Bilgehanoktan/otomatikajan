"""
core/agi/immunity/antibody_test_429.py — Cognitive Immunity Patch

Faz 12.1: 429 (Rate Limit) hatalarının yol açtığı "hallucination pressure" (halüsinasyon baskısı) 
durumunda sistemin otonom olarak 'Safe Mode'a geçmesini ve termal soğutma (backoff) 
uygulamasını sağlar.
"""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger("agi.immunity.429")

class RateLimitAntibody:
    """
    429 hatalarını izleyen ve bilişsel dürüstlüğü korumak için 
    müdahale eden otonom mekanizma.
    """
    
    def __init__(self):
        self.failure_count = 0
        self.last_failure = None
        self.is_cooling_down = False
        self.cooldown_until = None

    async def report_failure(self, error_msg: str = ""):
        """429 hatası tespit edildiğinde çağrılır."""
        self.failure_count += 1
        self.last_failure = datetime.now(timezone.utc)
        
        logger.warning(f"[ANTIBODY] 429 Rate Limit detected! Failure count: {self.failure_count}")
        
        if self.failure_count >= 3:
            await self.activate_cooldown()

    async def activate_cooldown(self, duration_sec: int = 60):
        """Sistemi soğutma (backoff) moduna sokar."""
        self.is_cooling_down = True
        self.cooldown_until = datetime.now(timezone.utc).timestamp() + duration_sec
        logger.critical(f"[ANTIBODY] CRITICAL LOAD: Entering Cooldown for {duration_sec}s. Hallucination pressure is high.")
        
        # Global Workspace'e veya Orchestrator'a sinyal gönderilebilir
        try:
            from services.orchestration.domain.events import event_bus
            await event_bus.emit(
                "agi.cooldown_start", 
                duration=duration_sec, 
                reason="rate_limit_pressure",
                agent_id="antibody_429"
            )
        except Exception:
            pass

    def check_status(self) -> bool:
        """Sistemin çalışmaya devam edip edemeyeceğini döner."""
        if not self.is_cooling_down:
            return True
            
        now = datetime.now(timezone.utc).timestamp()
        if now >= (self.cooldown_until or 0):
            self.is_cooling_down = False
            self.failure_count = 0
            logger.info("[ANTIBODY] Cooldown finished. System integrity restored.")
            return True
            
        return False

# Singleton instance
antibody_429 = RateLimitAntibody()
