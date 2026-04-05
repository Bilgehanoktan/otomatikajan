import time
import pytest
from llm.llm_types import ProviderStats
from core.agi.consciousness.affective_core import AffectiveCore

def test_rolling_average_latency():
    stats = ProviderStats()
    
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
    assert len(stats.latencies_window) == 10

def test_dynamic_quarantine_scaling():
    stats = ProviderStats()
    
    # Case 1: Simple failure
    stats.record_error("Generic Error")
    # Base is 5 min (300s)
    assert 295 <= (stats.quarantine_until - time.time()) <= 305
    
    # Case 2: Consecutive failure
    stats.record_error("Retry Error")
    # Should scale (e.g. 10m - 600s)
    # Check if it increased
    assert (stats.quarantine_until - time.time()) > 305
    
    # Case 3: Rate Limit (429) should be immediate high penalty
    stats.record_error("Rate Limit Error (429)")
    # Should be capped or high
    assert (stats.quarantine_until - time.time()) >= 900 # >= 15m

def test_passive_metabolism():
    core = AffectiveCore()
    core.internal_stress = 0.8
    core.energy = 0.2
    
    # Mocking time passing would be hard, so we just call the private method
    # or ensure it reflects in get_state_matrix
    
    # Simulate some "idle" time by manually setting last_metabolism_check
    core.last_metabolism_check = time.time() - 60 # 1 minute ago
    
    state = core.get_state_matrix()
    
    # Stress should have decreased from 0.8
    assert state["internal_stress"] < 0.8
    # Energy should have increased from 0.2
    assert state["energy"] > 0.2

if __name__ == "__main__":
    test_rolling_average_latency()
    test_dynamic_quarantine_scaling()
    test_passive_metabolism()
    print("Metabolic Pacing V88 Tests Passed!")
