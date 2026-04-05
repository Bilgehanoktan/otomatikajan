import time
import pytest
from llm.llm_types import ProviderStats
from core.agi.consciousness.affective_core import AffectiveCore

def test_rolling_average_latency():
    stats = ProviderStats("test", "test_key", "http://test", "test-model")
    
    # 1. Add some initial latencies
    for _ in range(5):
        stats.record_success(0.5)
    
    assert stats.avg_latency == 0.5
    
    # 2. Add high latency (should use only last 10, but currently we have 5)
    for _ in range(5):
        stats.record_success(1.5)
        
    assert stats.avg_latency == 1.0 # (5*0.5 + 5*1.5)/10
    
    # 3. Add more to push out old ones
    for _ in range(10):
        stats.record_success(2.0)
        
    # Now top 10 should be all 2.0
    assert stats.avg_latency == 2.0
    assert len(stats.latency_window) == 10

def test_dynamic_quarantine_scaling():
    stats = ProviderStats("test", "test_key", "http://test", "test-model")
    
    # Case 1: Simple failure
    stats.record_failure("Generic Error")
    # Base is 5 min (300s)
    assert 290 <= (stats.quarantine_until - time.time()) <= 310
    
    # Case 2: Consecutive failure
    stats.record_failure("Retry Error")
    # Should scale (e.g. 10m - 600s)
    # Check if it increased
    assert (stats.quarantine_until - time.time()) > 310
    
    # Case 3: Rate Limit (429) should be immediate high penalty
    stats.record_failure("Rate Limit Error (429)")
    # Should be capped or high
    assert (stats.quarantine_until - time.time()) >= 900 # >= 15m

def test_passive_metabolism():
    core = AffectiveCore()
    core.state["internal_stress"] = 0.8
    core.state["energy_reserve"] = 0.2
    
    # Simulate some "idle" time by manually setting last_decay_time
    # _last_decay_time is internal, we need to bypass cooldown (10s)
    core._last_decay_time = time.time() - 3600 # 1 hour ago
    
    state = core.get_state_matrix()
    
    # Stress should have decreased from 0.8
    assert state["internal_stress"] < 0.8
    # Energy should have increased from 0.2
    assert state["energy_reserve"] > 0.2

if __name__ == "__main__":
    test_rolling_average_latency()
    test_dynamic_quarantine_scaling()
    test_passive_metabolism()
    print("Metabolic Pacing V88 Tests Passed!")
