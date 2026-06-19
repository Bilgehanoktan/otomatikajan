
import pytest
from services.improve.benchmark_loader import RepairBenchLoader

def test_loader_loads_all_cases():
    loader = RepairBenchLoader()
    cases = loader.list_all_cases() # Fixed method name
    assert len(cases) >= 3
    assert any(c.id == "re-001-replay-bug" for c in cases) # Fixed attribute name

def test_loader_loads_specific_case():
    loader = RepairBenchLoader()
    case = loader.load_case("re-002-cost-anomaly")
    assert case is not None
    assert "current_hourly_spend" in case.input_context # Corrected key
