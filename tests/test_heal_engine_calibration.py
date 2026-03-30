import pytest
import asyncio
from unittest.mock import MagicMock, patch
from core.heal_engine import SelfHealEngine
from heal.agent_state import AgentSnapshot, AgentState

@pytest.fixture
def mock_orch():
    orch = MagicMock()
    orch.get_health.return_value = {"orchestrator": 1.0}
    return orch

@pytest.mark.asyncio
async def test_ewma_smoothing_spike(mock_orch):
    """VERIFICATION: Tekil bir latency spike skoru hemen düşürmemeli (Smoothing)."""
    engine = SelfHealEngine(mock_orch)
    engine._last_latency_ewma = 5.0
    engine._alpha = 0.2
    
    snap = AgentSnapshot(agent_id="orchestrator", state=AgentState.HEALTHY, score=1.0)
    snap.record_latency(120.0) 
    engine._snaps["orchestrator"] = snap
    
    score = engine.system_health_score()
    print(f"DEBUG EWMA Spike: latency={engine._last_latency_ewma}, score={score}")
    
    assert score > 0.85
    assert engine._last_latency_ewma < 40.0

@pytest.mark.asyncio
async def test_ewma_sustained_stress(mock_orch):
    """VERIFICATION: Sürekli (sustained) stres durumunda skor kademeli olarak düşmeli."""
    engine = SelfHealEngine(mock_orch)
    engine._last_latency_ewma = 5.0
    engine._alpha = 0.2 # Test için yumuşatma (0.2 * 80 + 0.8 * 5 = 20)
    
    snap = AgentSnapshot(agent_id="orchestrator", state=AgentState.HEALTHY, score=1.0)
    snap.record_latency(80.0) 
    engine._snaps["orchestrator"] = snap
    
    scores = []
    for i in range(5):
        s = engine.system_health_score()
        scores.append(s)
        print(f"DEBUG EWMA Sustained {i}: latency={engine._last_latency_ewma:.2f}, score={s:.4f}")
        
    assert scores[-1] < 1.0, f"Skor hiç düşmedi: {scores}"
    assert scores[-1] < scores[0], f"Skor zamanla azalmadı: {scores}"

@pytest.mark.asyncio
async def test_memory_threshold_graduation(mock_orch):
    """VERIFICATION: 1200MB altındaki bellek kullanımı ceza almamalı (Faz 12.1 Baseline)."""
    engine = SelfHealEngine(mock_orch)
    engine._last_mem_ewma = 300.0
    
    # Mocking psutil.Process instance instead of the class
    with patch("psutil.Process") as mock_ps_class:
        mock_p = MagicMock()
        mock_p.memory_info.return_value.rss = 1100 * 1024 * 1024 # 1100MB
        mock_ps_class.return_value = mock_p
        
        with patch("os.getpid", return_value=123):
             score = engine.system_health_score()
             print(f"DEBUG Mem: ewma={engine._last_mem_ewma:.2f}, score={score}")
             assert score == 1.0
