"""
llm/cost_calc.py — Saf Maliyet Hesaplama (RC1)

DB bağımlılığı yok — import anında hiçbir ağır paket yüklenmez.
cost_tracker.py bu modülü kullanır, testler doğrudan bunu import edebilir.
"""

# ── Fiyat Tablosu (USD / 1M token) ──────────────────────────
PRICING: dict[str, dict[str, float]] = {
    "gpt-4o":                     {"input": 2.5,   "output": 10.0},
    "gpt-4o-mini":                {"input": 0.15,  "output": 0.60},
    "claude-3-5-sonnet-20241022": {"input": 3.0,   "output": 15.0},
    "claude-3-5-haiku-20241022":  {"input": 0.80,  "output": 4.0},
    "gemini-1.5-pro":             {"input": 1.25,  "output": 5.0},
    "gemini-1.5-flash":           {"input": 0.075, "output": 0.30},
    "qwen/qwen3.5-397b-a17b":     {"input": 2.5,   "output": 10.0},
    # fallback
    "default":                    {"input": 1.0,   "output": 3.0},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Model, input ve output token sayısına göre USD maliyet hesapla.
    DB veya başka bağımlılık gerektirmez.
    """
    pricing = PRICING.get(model) or PRICING.get("default")
    input_cost  = (input_tokens  / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 8)


def estimate_tokens(text: str) -> int:
    """Metin uzunluğundan yaklaşık token sayısı tahmin et (4 char = 1 token)."""
    return max(1, len(text) // 4)


def format_cost(usd: float) -> str:
    """Maliyet değerini okunabilir formatta döndür."""
    if usd < 0.001:
        return f"${usd * 1000:.4f}m"   # milli-dolar
    return f"${usd:.4f}"


def budget_check(spent_usd: float, budget_usd: float) -> dict:
    """Bütçe kontrolü — DB yok."""
    pct = (spent_usd / budget_usd * 100) if budget_usd > 0 else 0.0
    return {
        "spent":     spent_usd,
        "budget":    budget_usd,
        "remaining": max(0.0, budget_usd - spent_usd),
        "pct_used":  round(pct, 1),
        "over_budget": spent_usd > budget_usd,
    }



def cost_summary(records: list[dict] | list[object]) -> dict:
    """Basit maliyet özeti — test ve legacy uyumluluğu için."""
    total_cost = 0.0
    total_calls = len(records)
    for r in records:
        cost = r.get('cost_usd', 0.0) if isinstance(r, dict) else getattr(r, 'cost_usd', 0.0)
        total_cost += float(cost or 0.0)
    return {
        "total_calls": total_calls,
        "total_cost_usd": round(total_cost, 6),
    }
