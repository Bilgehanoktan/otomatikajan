import pytest
import time
import asyncio
from unittest.mock import MagicMock, patch
from packages.llm_gateway.model_orchestrator import ProviderStats, CircuitState
from api.resilience import CircuitBreaker, CircuitState as APICircuitState

def test_llm_latency_quarantine():
    """LLM sağlayıcısının yavaş yanıtlar sonrası karantinaya alınmasını test eder."""
    stats = ProviderStats(
        name="test_provider", 
        api_key_env="TEST_KEY", 
        base_url="http://test", 
        model="test-model"
    )
    
    # Threshold: 15s. 3 kez 16s gönderiyoruz.
    stats.record_success(16.0)
    assert stats.latency_streak == 1
    stats.record_success(16.0)
    assert stats.latency_streak == 2
    
    stats.record_success(16.0)
    assert stats.latency_streak == 3
    assert stats.quarantine_until > time.time()
    assert stats.is_available() is False

def test_llm_latency_recovery():
    """Hızlı bir yanıtın latency_streak'i sıfırladığını test eder."""
    stats = ProviderStats(
        name="test_provider", 
        api_key_env="TEST_KEY", 
        base_url="http://test", 
        model="test-model"
    )
    
    stats.record_success(16.0)
    stats.record_success(16.0)
    assert stats.latency_streak == 2
    
    stats.record_success(1.0) # Hızlı yanıt
    assert stats.latency_streak == 0
    assert stats.quarantine_until == 0.0

def test_api_circuit_breaker_flow():
    """API Circuit Breaker'ın hata sonrası devreyi açmasını ve recovery sürecini test eder."""
    breaker = CircuitBreaker("test_api", fail_threshold=2, recovery_timeout=0.1)
    
    assert breaker.is_available() is True
    
    breaker.record_failure()
    assert breaker.state == APICircuitState.CLOSED
    
    breaker.record_failure()
    assert breaker.state == APICircuitState.OPEN
    assert breaker.is_available() is False
    
    # Recovery timeout bekle
    time.sleep(0.15)
    assert breaker.is_available() is True
    assert breaker.state == APICircuitState.HALF_OPEN
    
    breaker.record_success()
    assert breaker.state == APICircuitState.CLOSED

@pytest.mark.asyncio
async def test_circuit_breaker_decorator():
    """Decorator'ın istisnaları yakalayıp devreyi etkileyip etkilemediğini test eder."""
    from api.resilience import circuit_breaker
    from fastapi import HTTPException
    
    breaker_name = "decorated_test"
    
    @circuit_breaker(name=breaker_name, fail_threshold=1)
    async def failing_func():
        raise RuntimeError("Boom")
        
    try:
        await failing_func()
    except RuntimeError:
        pass
        
    from api.resilience import get_breaker
    breaker = get_breaker(breaker_name)
    assert breaker.state == APICircuitState.OPEN
    
    # Bir sonraki çağrı 503 fırlatmalı
    with pytest.raises(HTTPException) as exc:
        await failing_func()
    assert exc.value.status_code == 503
