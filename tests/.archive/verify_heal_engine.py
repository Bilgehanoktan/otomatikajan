import asyncio
import logging
import time
from core.heal_engine import heal_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_heal_engine")

async def test_system_health_scoring():
    logger.info("Testing HealEngine Systemic Health Scoring...")
    
    # 1. Base State (Healthy)
    heal_engine._db_available = True
    heal_engine._error_rate = 0.0
    score_nominal = heal_engine.system_health_score()
    logger.info(f"Nominal Score: {score_nominal}")
    assert score_nominal > 0.9
    
    # 2. High Error Rate (>35%)
    heal_engine._error_rate = 0.4
    score_high_error = heal_engine.system_health_score()
    logger.info(f"High Error Score (40% error): {score_high_error}")
    assert score_high_error < score_nominal
    assert score_high_error < 0.6 # Penalty should be significant
    
    # 3. DB Unavailable
    heal_engine._db_available = False
    score_db_offline = heal_engine.system_health_score()
    logger.info(f"DB Offline Score: {score_db_offline}")
    assert score_db_offline < 0.3 # Should be very low
    
    logger.info("✓ Test Passed: HealEngine reflects systemic health.")

if __name__ == "__main__":
    asyncio.run(test_system_health_scoring())
