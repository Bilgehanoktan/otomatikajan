import time
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# ── 1. Canonical Çıktı Sözleşmesi ────────────────────────
class LLMResponse(BaseModel):
    content: str
    input_tokens: int
    output_tokens: int
    model_name: str
    provider: str
    latency_s: float
    cost_usd: float

# ── 2. Devre Kesici (Circuit Breaker) Durumları ──────────
class CircuitState(str, Enum):
    CLOSED    = "closed"     # Normal çalışma
    OPEN      = "open"       # Devre açık, istekler geçmiyor
    HALF_OPEN = "half_open"  # Test modunda

@dataclass
class ProviderStats:
    name:           str
    api_key_env:    str
    base_url:       str
    model:          str
    history:        List[bool]   = field(default_factory=list)
    latencies:      List[float]  = field(default_factory=list)
    success:        int          = 0
    failure:        int          = 0
    total_latency:  float        = 0.0
    last_failure:   float        = 0.0
    circuit:        CircuitState = CircuitState.CLOSED
    penalty_multiplier: int      = 1
    quarantine_until:   float    = 0.0  # Otonom Karantina (Faz 12.1)
    latency_streak:     int      = 0    # Ardışık yavaşlama sayısı (Faz 12.3)

    OPEN_THRESHOLD:    int   = field(default=3,    init=False, repr=False)
    HALF_OPEN_AFTER:   float = field(default=30.0, init=False, repr=False)
    WINDOW_SIZE:       int   = field(default=10,   init=False, repr=False)
    LATENCY_THRESHOLD: float = field(default=15.0, init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "_fail_streak", 0)

    @property
    def health_score(self) -> float:
        if not self.history: return 1.0
        recent_success_rate = sum(self.history) / len(self.history)
        latency_penalty = 1.0
        avg = self.avg_latency
        if avg > 5.0:
            latency_penalty = max(0.4, 1.0 - (avg - 5.0) / 10.0)
        base = recent_success_rate * latency_penalty
        if self.quarantine_until > time.time(): return 0.0
        if self.circuit == CircuitState.OPEN: base = 0.0
        elif self.circuit == CircuitState.HALF_OPEN: base *= 0.3
        return round(float(base), 3)

    @property
    def avg_latency(self) -> float:
        # Phase 12.5 Scaling: Use moving window (last 10) instead of all-time totals
        if self.latencies:
            return round(sum(self.latencies) / len(self.latencies), 2)
        total = self.success + self.failure
        return round(float(self.total_latency / total), 2) if total else 0.0

    def record_success(self, latency: float):
        now = time.time()
        was_quarantined = self.quarantine_until > now
        was_open = self.circuit == CircuitState.OPEN

        self.success      += 1
        self.total_latency += latency
        self.penalty_multiplier = 1
        self.latency_streak     = 0 # Reset streak on success
        self.circuit       = CircuitState.CLOSED
        self.quarantine_until = 0.0 # Clear quarantine on success
        
        self.history.append(True)
        self.latencies.append(latency)
        if len(self.history) > self.WINDOW_SIZE:
            self.history.pop(0)
            self.latencies.pop(0)

        # Olay yayınla
        if was_quarantined or was_open:
            try:
                from core.events import event_bus
                import asyncio
                asyncio.create_task(event_bus.emit(
                    "provider.recovered",
                    provider=self.name,
                    message=f"Sağlayıcı {self.name} başarıyla iyileşti ve tekrar aktif.",
                    severity="info"
                ))
            except Exception: pass

    def record_failure(self, error_msg: str = ""):
        """FAZ 88: Dinamik karantina ve 429 hata yakalama."""
        self.failure      += 1
        self.last_failure  = time.time()
        self.history.append(False)
        if len(self.history) > self.WINDOW_SIZE:
            self.history.pop(0)
        
        # 1. Multiplier artışı (Hatalar üst üste geldikçe bekleme süresi artar)
        self.penalty_multiplier = min(self.penalty_multiplier * 2, 32)
        
        # 2. Dinamik Karantina Süresi (5m - 30m arası)
        is_rate_limit = "429" in str(error_msg) or "rate limit" in str(error_msg).lower()
        
        # 429 ise doğrudan yüksek penaltı (15m base), değilse 5m base
        base_seconds = 900 if is_rate_limit else 300
        duration = min(base_seconds * (self.penalty_multiplier // 2), 1800)
        
        self.quarantine_until = time.time() + duration
        
        if self.history.count(False) >= self.OPEN_THRESHOLD:
            self.circuit = CircuitState.OPEN
            
        logger.warning(f"[AGI-METABOLISM] {self.name} failure recorded. Reason: {error_msg}. Quarantined for {duration}s.")

        # Karantina olayını yayınla
        try:
            from core.events import event_bus
            import asyncio
            asyncio.create_task(event_bus.emit(
                "provider.quarantined",
                provider=self.name,
                duration_s=duration,
                reason=error_msg,
                message=f"Sağlayıcı {self.name} karantinaya alındı ({duration}s). Neden: {error_msg}",
                severity="warning"
            ))
        except Exception: pass

    def is_available(self) -> bool:
        now = time.time()
        # 1. Karantina kontrolü (Dinamik Phase 88)
        if self.quarantine_until > now: 
            return False
            
        # 2. Circuit Breaker kontrolü
        if self.circuit in (CircuitState.CLOSED, CircuitState.HALF_OPEN): 
            return True
            
        cooldown = self.HALF_OPEN_AFTER * self.penalty_multiplier
        if self.circuit == CircuitState.OPEN and (now - self.last_failure > cooldown):
            self.circuit = CircuitState.HALF_OPEN
            return True
        return False

    @property
    def api_key(self) -> str:
        return os.getenv(self.api_key_env, "")

    def is_placeholder_key(self) -> bool:
        if self.name == "anthropic" and os.getenv("ANTHROPIC_AUTH_TOKEN"):
            return False
        key = self.api_key
        if not key: return True
        placeholders = ["sk-...", "sk-ant-...", "AI...", "your-", "key-", "...", "abc...", "YOUR_API_KEY", "YOUR_OPENAI_KEY", "PLACEHOLDER"]
        if any(key == p for p in placeholders): return True
        if len(key) < 20: return True
        return False

# ── 3. Sağlayıcılar Listesi ──────────────────────────────
PROVIDERS: list[ProviderStats] = [
    ProviderStats(name="openai", api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com/v1/chat/completions", model="gpt-4o-mini"),
    ProviderStats(name="anthropic", api_key_env="ANTHROPIC_API_KEY", base_url="https://api.anthropic.com/v1/messages", model="claude-3-5-haiku-20241022"),
    ProviderStats(name="gemini", api_key_env="GEMINI_API_KEY", base_url="https://generativelanguage.googleapis.com", model="gemini-2.0-flash"),
    ProviderStats(name="groq", api_key_env="GROQ_API_KEY", base_url="https://api.groq.com/openai/v1/chat/completions", model="llama-3.3-70b-versatile"),
    ProviderStats(name="openrouter", api_key_env="OPENROUTER_API_KEY", base_url="https://openrouter.ai/api/v1/chat/completions", model="meta-llama/llama-3.1-70b-instruct"),
    ProviderStats(name="nvidia", api_key_env="NVIDIA_API_KEY", base_url="https://integrate.api.nvidia.com/v1/chat/completions", model="qwen/qwen3.5-397b-a17b"),
    ProviderStats(name="moonshot", api_key_env="MOONSHOT_API_KEY", base_url="https://api.moonshot.cn/v1/chat/completions", model="moonshot-v1-8k"),
    ProviderStats(name="deepseek", api_key_env="DEEPSEEK_API_KEY", base_url="https://api.deepseek.com/chat/completions", model="deepseek-chat"),
]
