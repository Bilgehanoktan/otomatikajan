import asyncio
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import logging
import httpx
import random

from services.observability.logging import get_logger
from libs.observability.tracer import traced, span

logger = get_logger("libs.llm.model_orchestrator")
_LAST_PROVIDER_STATUS_FINGERPRINT: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]] | None = None
_ERROR_LOG_WINDOW_SECONDS = 60.0
_ERROR_LOG_STATE: dict[tuple[str, str], tuple[float, int]] = {}

def _log_with_throttle(kind: str, provider: str, message: str) -> None:
    now = time.time()
    key = (kind, provider)
    started_at, suppressed = _ERROR_LOG_STATE.get(key, (now, 0))

    if now - started_at >= _ERROR_LOG_WINDOW_SECONDS:
        if suppressed > 0:
            logger.warning(
                "[THROTTLE] %s/%s suppressed %s repeated events in last %ss.",
                kind,
                provider,
                suppressed,
                int(_ERROR_LOG_WINDOW_SECONDS),
            )
        _ERROR_LOG_STATE[key] = (now, 0)
        logger.warning(message)
        return

    if suppressed == 0:
        logger.warning(message)
    _ERROR_LOG_STATE[key] = (started_at, suppressed + 1)

# ── 1. Canonical Çıktı Sözleşmesi ────────────────────────
class LLMResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

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

    OPEN_THRESHOLD:    int   = field(default=5,    init=False, repr=False)
    HALF_OPEN_AFTER:   float = field(default=5.0,  init=False, repr=False)
    WINDOW_SIZE:       int   = field(default=10,   init=False, repr=False)
    LATENCY_THRESHOLD: float = field(default=15.0, init=False, repr=False) # Karantina sınırı

    def __post_init__(self):
        object.__setattr__(self, "_fail_streak", 0)
        # Faz 12.1: Dynamic config override from environment
        prefix = self.name.upper()
        env_base = os.getenv(f"{prefix}_BASE_URL")
        if env_base:
            self.base_url = env_base
        env_model = os.getenv(f"{prefix}_MODEL")
        if env_model:
            self.model = env_model

    @property
    def health_score(self) -> float:
        if not self.history: return 1.0

        # Recent success rate
        recent_success_rate = sum(self.history) / len(self.history)

        # Latency Penalty (Slow models are less preferred)
        latency_penalty = 1.0
        avg = self.avg_latency
        if avg > 5.0:  # If slower than 5 seconds
            # Score drops linearly between 5s and 15s
            latency_penalty = max(0.4, 1.0 - (avg - 5.0) / 10.0)

        base = recent_success_rate * latency_penalty

        # Karantina Kontrolü
        if self.quarantine_until > time.time():
            return 0.0

        if self.circuit == CircuitState.OPEN: base = 0.0
        elif self.circuit == CircuitState.HALF_OPEN: base *= 0.3
        return round(base, 3)

    @property
    def avg_latency(self) -> float:
        total = self.success + self.failure
        return round(self.total_latency / total, 2) if total else 0.0

    def record_success(self, latency: float):
        self.success      += 1
        self.total_latency += latency
        self.penalty_multiplier = 1
        self.circuit       = CircuitState.CLOSED

        # Faz 12.3: Gecikme Kontrolü
        if latency > self.LATENCY_THRESHOLD:
            self.latency_streak += 1
            if self.latency_streak >= 3:
                self.quarantine_until = time.time() + 1800 # 30 dk karantina
                logger.warning(f"GECİKME KARANTİNASI: {self.name} ardışık {self.latency_streak} yavaş yanıt nedeniyle 30dk askıya alındı.")
        else:
            self.latency_streak = 0

        self.history.append(True)
        self.latencies.append(latency)
        if len(self.history) > self.WINDOW_SIZE:
            self.history.pop(0)
            self.latencies.pop(0)

    def record_failure(self, is_rate_limit: bool = False):
        self.failure      += 1
        self.last_failure  = time.time()
        self.history.append(False)
        if len(self.history) > self.WINDOW_SIZE:
            self.history.pop(0)

        # Increase backoff penalty
        penalty_step = 1.1 # Further reduced from 1.2 to be ultra-permissive
        self.penalty_multiplier = int(min(self.penalty_multiplier * penalty_step, 64))

        if self.history.count(False) >= self.OPEN_THRESHOLD or is_rate_limit:
            self.circuit = CircuitState.OPEN
            log_level = logging.WARNING if is_rate_limit else logging.ERROR
            logger.log(log_level, f"Devre Kesici AÇILDI ({'429' if is_rate_limit else 'OPEN'}): {self.name}. Ceza: {self.penalty_multiplier}x")

            # Otonom Karantina (Eğer çok sık hata alıyorsa 1 saat kapat)
            # 429'lar için daha müsamahakarız
            quarantine_limit = 32 if is_rate_limit else 16
            if self.penalty_multiplier >= quarantine_limit:
                self.quarantine_until = time.time() + 3600
                if is_rate_limit:
                    logger.warning(f"OTONOM KARANTİNA: {self.name} kronik rate limit nedeniyle 1 saat askıya alındı.")
                else:
                    logger.critical(f"OTONOM KARANTİNA (BAN): {self.name} kronik hata nedeniyle 1 saat yasaklandı.")

    def is_available(self) -> bool:
        if self.quarantine_until > time.time():
            return False

        if self.circuit in (CircuitState.CLOSED, CircuitState.HALF_OPEN): return True
        # Backoff adjusts the duration
        # 429 rate limit errors increase the penalty_multiplier rapidly
        cooldown = self.HALF_OPEN_AFTER * self.penalty_multiplier
        if self.circuit == CircuitState.OPEN and (time.time() - self.last_failure > cooldown):
            self.circuit = CircuitState.HALF_OPEN
            logger.info(f"Devre Kesici YARI-AÇIK (HALF-OPEN): {self.name} test ediliyor.")
            return True
        return False

    def maybe_half_open(self) -> bool:
        """Legacy compat (RC1): is_available() ile aynı davranış."""
        return self.is_available()

    @property
    def api_key(self) -> str:
        return os.getenv(self.api_key_env, "")

    def is_placeholder_key(self) -> bool:
        """API anahtarının bir placeholder (örnek değer) olup olmadığını kontrol eder."""
        key = self.api_key
        if not key: return True

        # Bilinen placeholder değerleri ve desenleri
        placeholders = [
            "sk-...", "sk-ant-...", "AI...", "your-", "key-", "...", "abc...",
            "YOUR_API_KEY", "YOUR_OPENAI_KEY", "PLACEHOLDER"
        ]

        # Eğer anahtar listedeki bir placeholder'a tam eşitse
        if any(key == p for p in placeholders):
            return True

        # Çok kısa anahtarlar da muhtemelen placeholder'dır (gerçek anahtarlar genelde 30+ karakter)
        if len(key) < 20:
            return True

        # Faz 12.1: OpenRouter/Proxy Check
        is_proxy = "openrouter.ai" in (self.base_url or "").lower()

        # Provider-format guard:
        # Wrong provider key in wrong env (for example OPENROUTER key in ANTHROPIC var)
        # should be treated as invalid to prevent noisy/broken fallback attempts.
        expected_prefixes = {
            "openai": ("sk-", "sk-proj-"),
            "anthropic": ("sk-ant-",),
            "gemini": ("AIza",),
            "groq": ("gsk_",),
            "openrouter": ("sk-or-v1-",),
            "nvidia": ("nvapi-",),
            "moonshot": ("sk-",),
            "deepseek": ("sk-",),
        }
        prefixes = expected_prefixes.get(self.name, ())

        # If it's a proxy, we allow OpenRouter prefix even for 'anthropic'
        if is_proxy and key.startswith("sk-or-v1-"):
            return False

        if prefixes and not key.startswith(prefixes):
            return True

        return False

# ── 3. Sağlayıcılar ve Rota Politikası ───────────────────
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

# V2 Mimari: Ajan rolüne göre model hiyerarşisi (isimler PROVIDERS ile eşleşmeli)
ROUTING_POLICY: dict[str, list[str]] = {
    # Architect: High-end models for decision making
    "architect": ["nvidia", "anthropic", "openai", "groq", "openrouter", "gemini"],

    # Backend Dev: Coding expertise
    "backend_dev": ["nvidia", "openai", "groq", "openrouter", "gemini", "anthropic"],

    # QA Engineer: Large context and speed (Balanced)
    "qa_engineer": ["openai", "gemini", "groq", "openrouter"],

    # Security: Precise and strict
    "security": ["nvidia", "anthropic", "openai", "groq"],

    # Tech Writer: Fluent and cheap
    "tech_writer": ["gemini", "openai", "groq", "openrouter", "anthropic"],

    # System Controller: Decision/Planning
    "system_controller": ["openai", "groq", "anthropic", "gemini"],

    # Strategist: Planning/Reasoning
    "strategist": ["nvidia", "anthropic", "openai", "groq"],

    # Visual Auditor: Vision-capable models
    "visual_auditor": ["gemini", "openai", "groq"],

    # General fallback: Distributed load
    "general": ["openai", "gemini", "groq", "openrouter", "anthropic"]
}

_COST_PER_1K: dict[str, float] = {
    "openai":    0.00015,
    "anthropic": 0.00025,
    "gemini":    0.000075,
    "groq":      0.0001,
    "openrouter": 0.0002,
    "nvidia":     0.0003,
    "moonshot":   0.00015, # Estimated
    "deepseek":   0.0001,  # Estimated
}

class ModelOrchestrator:
    """
    V2 Mimari: Ajanlardan gelen istekleri alır, ROUTING_POLICY'ye göre
    sağlayıcıları (fallback zinciriyle) dener, devre kesiciyi yönetir.
    """

    def __init__(self):
        self.providers = {p.name: p for p in PROVIDERS}
        self.economy_mode = False # Faz 12.2: Otonom tasarruf modu
        # Refresh config from env for all providers
        for p in self.providers.values():
            p.__post_init__()
        self._log_provider_status()

    async def generate(self, prompt: str, system_prompt: str = "Sen yardımcı bir AI asistansın.") -> str:
        """Orchestrator tarafından risk değerlendirmesi vb. için kullanılır."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        return await self.complete(messages)

    def _log_provider_status(self):
        global _LAST_PROVIDER_STATUS_FINGERPRINT
        found = []
        missing = []
        placeholders = []
        for p in self.providers.values():
            if not p.api_key:
                missing.append(p.name)
            elif p.is_placeholder_key():
                placeholders.append(p.name)
            else:
                found.append(p.name)

        fingerprint = (tuple(sorted(found)), tuple(sorted(placeholders)), tuple(sorted(missing)))
        if fingerprint == _LAST_PROVIDER_STATUS_FINGERPRINT:
            return
        _LAST_PROVIDER_STATUS_FINGERPRINT = fingerprint

        if found:
            logger.info(f"[LLM] Hazır sağlayıcılar: {', '.join(found)}")
        if placeholders:
            logger.warning(f"[LLM] Placeholder anahtar tespit edildi (atlanacak): {', '.join(placeholders)}")
        if missing:
            active_keys = {p for r in ROUTING_POLICY.values() for p in r}
            crit = [m for m in missing if m in active_keys]
            if crit:
                logger.debug(f"[LLM] Aktif rotalarda anahtar\u0131 eksik: {', '.join(crit)}")
            
            opts = [m for m in missing if m not in active_keys]
            if opts:
                logger.debug(f"[LLM] Opsiyonel sa\u011flay\u0131c\u0131lar (yap\u0131land\u0131r\u0131lmam\u0131\u015f): {', '.join(opts)}")


    async def get_fallback_chain(self, agent_role: str) -> List[str]:
        """Ajan rolüne göre sıralanmış (sağlık odaklı) sağlayıcı zincirini döner. (Tests/CEO compat)"""
        base_providers = ROUTING_POLICY.get(agent_role, ROUTING_POLICY["general"])
        available_stats = []
        for p_name in base_providers:
            p_stat = self.providers.get(p_name)
            if p_stat and p_stat.api_key and not p_stat.is_placeholder_key():
                available_stats.append(p_stat)

        # Health score'a göre sırala (azalan)
        available_stats.sort(key=lambda x: x.health_score, reverse=True)
        
        # Economy Mode Check
        if getattr(self, "economy_mode", False):
            # Ucuz modellere (örneğin gemini, openai gpt-4o-mini) öncelik ver
            cheap_providers = ["gemini", "openai", "groq", "deepseek"]
            available_stats.sort(key=lambda x: (x.name in cheap_providers, x.health_score), reverse=True)
            
        return [p.name for p in available_stats]

    @traced("ModelOrchestrator.complete_task")
    async def complete_task(
        self,
        agent_role: str,
        prompt: str,
        system_prompt: str,
        task_id: str = "unknown",
        project_id: str | None = None
    ) -> LLMResponse:
        # ── BÜTÇE KONTROLÜ (Phase 7) ──
        if project_id:
            try:
                from libs.db.session import AsyncSessionLocal
                from libs.db.models import Project
                async with AsyncSessionLocal() as db:
                    proj = await db.get(Project, project_id)
                    if proj and proj.budget_limit > 0 and proj.total_cost >= proj.budget_limit:
                        err_msg = f"Bütçe Aşıldı: Proje {proj.title} bütçesi (${proj.budget_limit}) tükendi."
                        logger.error(err_msg)
                        raise PermissionError(err_msg)
            except PermissionError: raise
            except Exception as e:
                logger.warning(f"Budget check error: {e}")

        # ── DİNAMİK PROMPT YAMASI ──
        try:
            from agents.prompts.prompt_manager import prompt_manager
            system_prompt = prompt_manager.apply_patch(agent_role, system_prompt)
        except Exception as e:
            logger.warning(f"Prompt patch hatası: {e}")

        # Ajanın rolüne göre fallback zincirini al
        base_providers = ROUTING_POLICY.get(agent_role, ROUTING_POLICY["general"])
        # LOAD BALANCING & HEALTH SORTING (Faz 12.1 Hardening):
        # Sağlayıcıları health_score'a göre sırala, en iyileri başa al.
        available_stats = []
        for p_name in base_providers:
            p_stat = self.providers.get(p_name)
            if p_stat and p_stat.api_key and not p_stat.is_placeholder_key():
                # Faz 12.2: Economy Mode devredeyse çok pahalı modelleri es geçebiliriz (Opsiyonel)
                if getattr(self, "economy_mode", False) and p_name in ["anthropic", "nvidia", "openrouter"]:
                    continue # Bütçe tehlikesinde bu sağlayıcıları hiç zincire alma
                available_stats.append(p_stat)

        # Health score'a göre sırala (azalan)
        available_stats.sort(key=lambda x: x.health_score, reverse=True)

        # En tepedeki 2 taneyi kendi içinde karıştır (Eşit sağlıkta olanları randomize et)
        top_tier = [p for p in available_stats if p.health_score >= 0.8]
        if len(top_tier) >= 2:
            random.shuffle(top_tier)
            preferred_providers = [p.name for p in top_tier] + [p.name for p in available_stats if p.health_score < 0.8]
        else:
            preferred_providers = [p.name for p in available_stats]

        last_error = None
        skipped_details = []

        for provider_name in preferred_providers:
            provider = self.providers.get(provider_name)

            if not provider:
                continue

            if not provider.api_key:
                skipped_details.append(f"{provider_name} (Key Yok)")
                continue

            if provider.is_placeholder_key():
                skipped_details.append(f"{provider_name} (Placeholder)")
                continue

            if not provider.is_available():
                skipped_details.append(f"{provider_name} (Circuit Open)")
                continue

            # API çağrısı için mesaj formatı
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            try:
                result = await self._call(provider, messages, max_tokens=2048, project_id=project_id)
                return result

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                
                # ── 402 Payment Required Handling (Faz 12.1 Hardening) ──
                if "402" in err_str or "payment" in err_str:
                    _log_with_throttle(
                        "provider_402",
                        provider.name,
                        f"PROVIDER BILLING (402): {provider.name} requires payment. Quarantining for 24h.",
                    )
                    provider.quarantine_until = time.time() + 86400
                    provider.circuit = CircuitState.OPEN
                    skipped_details.append(f"{provider.name} (402 Payment Required)")
                    continue

                # ── 429 Rate Limit (429) Handling ──
                is_rate_limit = "429" in err_str or "rate_limit" in err_str

                if is_rate_limit:
                    _log_with_throttle(
                        "provider_429",
                        provider.name,
                        f"RATE LIMIT (429) hit on {provider.name}. Applying progressive penalty and jitter delay.",
                    )
                    provider.record_failure(is_rate_limit=True)
                    skipped_details.append(f"{provider.name} (429 Rate Limit)")
                    
                    # Faz 13.04: Add randomized delay to reduce thundering herd pressure
                    jitter_delay = random.uniform(1.0, 5.0) * (provider.penalty_multiplier / 2)
                    await asyncio.sleep(min(jitter_delay, 2.0))
                else:
                    logger.warning(f"Sağlayıcı Hatası ({provider.name}): {str(e)}. Fallback modele geçiliyor.")
                    err_summary = str(e)[:50]
                    skipped_details.append(f"{provider.name} (Hata: {err_summary}...)")
                
                continue

        # ── EMERGENCY FALLBACK (Phase 12.1 Hardening) ──
        # Eğer tüm zincir tükendiyse ve durum kritiktse, 
        # en güvenilir sağlayıcıyı (openai veya gemini) devre açık olsa bile SON BİR KEZ dene.
        emergency_candidates = ["openai", "gemini"]
        for p_name in emergency_candidates:
            p = self.providers.get(p_name)
            if p and p.api_key and not p.is_placeholder_key():
                # Eğer son hatadan beri 10 saniye geçtiyse force-retry yap
                if time.time() - p.last_failure > 10.0:
                    logger.warning(f"EMERGENCY FALLBACK: {p_name} zorlanıyor (Tüm modeller kapalı!)")
                    try:
                        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
                        return await self._call(p, messages, max_tokens=2048, project_id=project_id)
                    except: pass

        # Eğer hala sonuç yoksa hata fırlat
        error_msg = f"Task {task_id} için tüm modeller başarısız oldu (Rol: {agent_role})."
        if skipped_details:
            error_msg += f" [Detaylar: {', '.join(skipped_details)}]"

        if last_error:
            error_msg += f" Son hata: {last_error}"
        else:
            error_msg += " Hiçbir geçerli sağlayıcı konfigüre edilmemiş veya erişilebilir değil."

        raise RuntimeError(error_msg)

    async def _call(
        self,
        provider: ProviderStats,
        messages: List[Dict],
        max_tokens: int,
        project_id: str | None = None
    ) -> LLMResponse:
        """Kalıcı API çağrısı, metrik kaydı ve hata yönetimi."""
        t0 = time.time()
        llm_timeout = float(os.getenv("LLM_TIMEOUT", "60.0"))

        # ── OTel Instrumentation (Phase 13.04) ──
        with span(f"llm_call:{provider.name}", attributes={
            "llm.provider": provider.name,
            "llm.model": provider.model,
            "llm.agent_role": "orchestrator", # Fallback default
            "project.id": project_id or "none",
        }) as s:
            try:
                async with httpx.AsyncClient(timeout=llm_timeout) as client:
                    if provider.name in ("openai", "groq", "openrouter"):
                        text = await self._call_openai(client, provider, messages, max_tokens)
                    elif provider.name == "anthropic":
                        text = await self._call_anthropic(client, provider, messages, max_tokens)
                    elif provider.name == "gemini":
                        text = await self._call_gemini(client, provider, messages, max_tokens)
                    elif provider.name == "nvidia":
                        text = await self._call_nvidia(client, provider, messages, max_tokens)
                    elif provider.name in ("moonshot", "deepseek"):
                        text = await self._call_openai(client, provider, messages, max_tokens)
                    else:
                        raise ValueError(f"Bilinmeyen sağlayıcı: {provider.name}")

                latency = time.time() - t0
                provider.record_success(latency)

                # Yaklaşık token ve maliyet hesabı
                est_tokens = self._estimate_tokens(messages)
                out_tokens = self._estimate_output_tokens(text)
                est_cost   = self._estimate_cost(provider.name, est_tokens, out_tokens)

                # Update span attributes
                s.set_attribute("llm.input_tokens", est_tokens)
                s.set_attribute("llm.output_tokens", out_tokens)
                s.set_attribute("llm.cost_usd", est_cost)
                s.set_attribute("llm.latency_s", latency)

                # Metrics ve Maliyet Kaydı
                try:
                    from services.observability.metrics import metrics
                    from libs.llm.cost_tracker import cost_tracker
                    from libs.db.session import AsyncSessionLocal

                    # In-memory metrics
                    metrics.record_llm_call(
                        provider=provider.name, latency_s=latency, success=True, tokens=est_tokens, cost_usd=est_cost
                    )

                    # In-memory Tracker & DB Persistence
                    rec = await cost_tracker.record(
                        provider=provider.name, model=provider.model, agent_id="orchestrator",
                        input_tokens=est_tokens, output_tokens=out_tokens,
                        latency_s=latency, success=True, project_id=project_id
                    )

                    # Arka planda DB'ye yaz
                    async with AsyncSessionLocal() as db:
                        await cost_tracker.persist(db, rec)
                        await db.commit()

                except Exception as e:
                    logger.warning(f"Cost tracking error: {e}")

                # Zorunlu Canonical Sözleşme Çıktısı
                return LLMResponse(
                    content=text,
                    input_tokens=est_tokens,
                    output_tokens=out_tokens,
                    model_name=provider.model,
                    provider=provider.name,
                    latency_s=latency,
                    cost_usd=est_cost
                )

            except Exception as _exc:
                provider.record_failure()
                try:
                    from services.observability.metrics import metrics
                    metrics.record_llm_call(provider=provider.name, latency_s=time.time() - t0, success=False)
                    metrics.record_error(f"llm.{provider.name}.{type(_exc).__name__}")
                except (ImportError, Exception):
                    pass
                raise _exc


    # ── RAW HTTP İSTEKLERİ ──────────────────────────────────
    # ── Token / Cost Yardımcı Metodları ─────────────────────────
    def _estimate_tokens(self, messages: list[dict]) -> int:
        """Mesaj listesinin yaklaşık token sayısını tahmin et."""
        return sum(len(str(m.get("content", ""))) // 4 for m in messages)

    def _estimate_output_tokens(self, text: str) -> int:
        """Üretilen metnin yaklaşık token sayısını tahmin et."""
        if not text: return 0
        return len(text) // 4

    def _estimate_cost(self, provider_name: str, input_tokens: int, output_tokens: int) -> float:
        """Token sayısından USD maliyet tahmini üret."""
        rate = _COST_PER_1K.get(provider_name, 0.0002)
        return round((input_tokens + output_tokens) / 1000 * rate, 6)

    async def _call_openai(self, client, p, messages, max_tokens) -> str:
        resp = await client.post(
            p.base_url,
            headers={"Authorization": f"Bearer {p.api_key}"},
            json={"model": p.model, "messages": messages, "max_tokens": max_tokens},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _call_nvidia(self, client, p, messages, max_tokens) -> str:
        # NVIDIA NIM API uses OpenAI format + optional thinking flag
        payload = {
            "model": p.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.60,
            "top_p": 0.95,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": True}
        }
        resp = await client.post(
            p.base_url,
            headers={"Authorization": f"Bearer {p.api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _call_anthropic(self, client, p, messages, max_tokens) -> str:
        # Anthropic 'system' rolünü ayrı bir parametre olarak ister
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        usr_msgs = [m for m in messages if m["role"] != "system"]

        # Faz 12.1: Use configured base_url (which handles overrides)
        base_url = p.base_url
        
        # Backward compat for explicit proxy env var if exists
        legacy_proxy = os.getenv("CLAUDE_PROXY_URL")
        if legacy_proxy:
            base_url = legacy_proxy

        is_openrouter = "openrouter.ai" in (base_url or "")
        if is_openrouter:
            if not (base_url or "").endswith("/chat/completions"):
                base_url = (base_url or "").rstrip("/") + "/chat/completions"
        elif base_url and not base_url.endswith("/messages"):
             if "/v1" not in base_url: base_url = base_url.rstrip("/") + "/v1/messages"
             else: base_url = base_url.rstrip("/") + "/messages"

        resp = await client.post(
            base_url,
            headers={
                "Authorization": f"Bearer {p.api_key}"
            } if is_openrouter else {
                "x-api-key": p.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": p.model, "messages": messages, "max_tokens": max_tokens} if is_openrouter else {"model": p.model, "max_tokens": max_tokens, "system": sys_msg, "messages": usr_msgs},
        )
        resp.raise_for_status()
        if is_openrouter:
            return resp.json()["choices"][0]["message"]["content"]
        return resp.json()["content"][0]["text"]

    async def _call_gemini(self, client, p, messages, max_tokens) -> str:
        # Gemini 'system' mesajını contents'in başına veya systemInstruction'a koyar.
        # Basitlik için tüm rolleri tek metin yapıyoruz.
        combined_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        contents = [{"parts": [{"text": combined_text}]}]

        # Dinamik URL oluşturma
        api_version = "v1beta"
        url = f"{p.base_url.rstrip('/')}/{api_version}/models/{p.model}:generateContent"

        resp = await client.post(
            f"{url}?key={p.api_key}",
            json={"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens}},
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    async def complete(
        self,
        messages: list[dict],
        preferred_agent: str = "general",
        max_tokens: int = 2048,
        force_provider: str | None = None,
    ) -> str:
        """Basitleştirilmiş arayüz — orchestrator, recovery, reviewer çağırır.

        Faz 12: Dynamic Model Routing ile karmaşıklığa göre provider seçilir.
        complete_task() ile aynı altyapıyı kullanır, doğrudan string döner.
        """
        # force_provider varsa doğrudan o sağlayıcıyı dene
        if force_provider:
            provider = self.providers.get(force_provider)
            if provider and provider.api_key and provider.is_available():
                result = await self._call(provider, messages, max_tokens)
                return result.content

        # Faz 12: Dynamic routing — prompt karmaşıklığına göre provider seç
        try:
            from libs.llm.model_router import get_model_router
            router   = get_model_router()
            prompt_text = " ".join(str(m.get("content", "")) for m in messages)
            decision = router.route(prompt_text, agent_role=preferred_agent)
            # force_provider üzerinden routing kararını uygula
            routed_provider = self.providers.get(decision.provider)
            if routed_provider and routed_provider.api_key and routed_provider.is_available():
                force_provider = decision.provider
                logger.debug(
                    f"Dynamic routing: {preferred_agent} -> {decision.provider}/{decision.model} "
                    f"[{decision.complexity.value}]"
                )
        except Exception:
            pass  # Routing hatası -> normal akış devam eder

        if force_provider:
            provider = self.providers.get(force_provider)
            if provider and provider.api_key and provider.is_available():
                try:
                    result = await self._call(provider, messages, max_tokens)
                    return result.content
                except Exception as e:
                    logger.warning(f"Routed provider {force_provider} failed: {e}. Falling back to normal chain.")

        # Mesajlardan system/user prompt'ları ayıkla
        system_prompt = ""
        user_prompt = ""
        for m in messages:
            if m.get("role") == "system":
                system_prompt = m.get("content", "")
            elif m.get("role") == "user":
                user_prompt = m.get("content", "")

        if not user_prompt:
            user_prompt = str(messages)

        result = await self.complete_task(
            agent_role=preferred_agent,
            prompt=user_prompt,
            system_prompt=system_prompt or "Sen yardımcı bir AI asistansın.",
        )
        return result.content

    async def complete_vision(self, prompt: str, images: list[str] | str, preferred_provider: str = "gemini") -> str:
        """Analyze one or more images using a vision-capable model (Gemini or OpenAI)."""
        if isinstance(images, str):
            images = [images]

        provider = self.providers.get(preferred_provider)
        if not provider or not provider.api_key or not provider.is_available():
            # Fallback to gemini if preferred is not available
            provider = self.providers.get("gemini")
            if not provider or not provider.api_key:
                provider = self.providers.get("openai")

        if not provider or not provider.api_key:
            raise RuntimeError("Vision support requires Gemini or OpenAI API key.")

        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if provider.name == "gemini":
                    # Gemini Vision format (Supports multiple parts)
                    parts: List[Dict[str, Any]] = [{"text": prompt}]
                    for img in images:
                        parts.append({"inline_data": {"mime_type": "image/png", "data": img}})

                    contents = [{"parts": parts}]
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{provider.model}:generateContent?key={provider.api_key}",
                        json={"contents": contents}
                    )
                    resp.raise_for_status()
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                elif provider.name == "openai":
                    # OpenAI Vision format
                    content_parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
                    for img in images:
                        content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}})

                    messages = [{"role": "user", "content": content_parts}]
                    resp = await client.post(
                        provider.base_url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                        json={"model": provider.model if "gpt-4o" in provider.model else "gpt-4o-mini", "messages": messages, "max_tokens": 1024}
                    )
                    resp.raise_for_status()
                    text = resp.json()["choices"][0]["message"]["content"]
                else:
                    raise ValueError(f"Vision not implemented for {provider.name}")

            latency = time.time() - t0
            provider.record_success(latency)

            # Phase 12.1: Vision Cost Tracking
            try:
                from libs.llm.cost_tracker import cost_tracker
                from libs.llm.cost_calc import estimate_tokens
                from libs.db.session import AsyncSessionLocal

                in_tokens = estimate_tokens(prompt)
                out_tokens = estimate_tokens(text)

                rec = await cost_tracker.record(
                    provider=provider.name, model=provider.model, agent_id="vision",
                    input_tokens=in_tokens, output_tokens=out_tokens,
                    latency_s=latency, success=True
                )
                async with AsyncSessionLocal() as db:
                    await cost_tracker.persist(db, rec)
                    await db.commit()
            except Exception as e:
                logger.warning(f"Vision cost tracking error: {e}")

            return text
        except Exception as e:
            provider.record_failure()
            logger.error(f"Vision API call failed ({provider.name}): {e}")
            raise e

    def provider_stats(self) -> list[dict]:
        """Arayüzde (Dashboard) devre kesici durumunu göstermek için."""
        return [
            {
                "name":          p.name,
                "health_score":  p.health_score,
                "circuit":       p.circuit,
                "quarantined":   p.quarantine_until > time.time(),
                "success":       p.success,
                "failure":       p.failure,
                "avg_latency_s": p.avg_latency,
            }
            for p in self.providers.values()
        ]

# ── Global Singleton Instance ──
model_orchestrator = ModelOrchestrator()
