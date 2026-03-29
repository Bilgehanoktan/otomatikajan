import pytest
from llm.cost_calc import calculate_cost, estimate_tokens, format_cost, budget_check

def test_calculate_cost_parity():
    """GPT-4o, Gemini ve Claude maliyetlerini kurshun geçirmezlik testi."""
    # GPT-4o (Input: 2.5, Output: 10.0 / 1M)
    # 1000 input, 1000 output -> 0.0025 + 0.010 = 0.0125
    assert calculate_cost("gpt-4o", 1000, 1000) == 0.0125
    
    # GPT-4o-mini (Input: 0.15, Output: 0.60 / 1M)
    # 1M input, 1M output -> 0.15 + 0.60 = 0.75
    assert calculate_cost("gpt-4o-mini", 1_000_000, 1_000_000) == 0.75
    
    # Gemini 1.5 Flash (Input: 0.075, Output: 0.30 / 1M)
    # 100k input, 100k output -> 0.0075 + 0.030 = 0.0375
    assert calculate_cost("gemini-1.5-flash", 100_000, 100_000) == 0.0375
    
    # Fallback (Default: 1.0, 3.0)
    assert calculate_cost("unknown-model", 1_000_000, 1_000_000) == 4.0

def test_estimate_tokens_parity():
    """4 karakter = 1 token kuralının doğrulanması."""
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcd" * 10) == 10
    assert estimate_tokens("") == 1 # Minimum 1 token guard'ı
    assert estimate_tokens("abc") == 1

def test_format_cost_parity():
    """Maliyet formatlamanın (milli-dollar vs USD) doğrulanması."""
    assert format_cost(0.0125) == "$0.0125"
    assert format_cost(0.0005) == "$0.5000m" # 0.5 milli-dollar
    assert format_cost(0.0) == "$0.0000m"
    assert format_cost(1.5) == "$1.5000"

def test_budget_check_parity():
    """Bütçe aşımı ve yüzde hesaplama doğrulanması."""
    # $5 harcanmış, $10 bütçe
    res = budget_check(5.0, 10.0)
    assert res["pct_used"] == 50.0
    assert res["remaining"] == 5.0
    assert res["over_budget"] is False
    
    # $11 harcanmış, $10 bütçe
    res = budget_check(11.0, 10.0)
    assert res["over_budget"] is True
    assert res["remaining"] == 0.0
    assert res["pct_used"] == 110.0
