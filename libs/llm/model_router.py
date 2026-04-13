"""
ModelRouter — Dynamic Model Routing (Faz 12)

Görevin karmaşıklığını, aciliyetini ve maliyeti analiz ederek
en uygun LLM modelini seçen katman.

Hiyerarşi:
  LOW    -> Ucuz & hızlı  (gpt-4o-mini, gemini-flash, claude-haiku)
  MEDIUM -> Dengeli       (gemini-pro, gpt-4o, claude-3-haiku)  
  HIGH   -> En güçlü      (claude-3-5-sonnet, gpt-4o, gemini-1.5-pro)
  CRITICAL -> Mutlaka doğru (claude-3-5-sonnet)

Tetikleyiciler:
  - Prompt uzunluğu
  - Kritik anahtar kelimeler (security, architecture, deadlock…)
  - Ajan rolü
  - Açık task tipi
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from services.observability.logging import get_logger
import asyncio

_log = get_logger("llm.model_router")


class TaskComplexity(str, Enum):
    LOW      = "low"       # Düzeltme, format, yorum, basit CRUD
    MEDIUM   = "medium"    # Test yazımı, standart API, refactor
    HIGH     = "high"      # Mimari karar, bug analizi, güvenlik
    CRITICAL = "critical"  # Self-repair, güvenlik açığı, race condition


# ── Model Katalog ────────────────────────────────────────────
# (mevcut PROVIDERS listesiyle örtüşmeli)
_MODEL_MAP: dict[str, dict[TaskComplexity, str]] = {
    "openai": {
        TaskComplexity.LOW:      "gpt-4o-mini",
        TaskComplexity.MEDIUM:   "gpt-4o-mini",
        TaskComplexity.HIGH:     "gpt-4o",
        TaskComplexity.CRITICAL: "gpt-4o",
    },
    "anthropic": {
        TaskComplexity.LOW:      "claude-3-5-haiku-20241022",
        TaskComplexity.MEDIUM:   "claude-3-5-haiku-20241022",
        TaskComplexity.HIGH:     "claude-3-5-sonnet-20241022",
        TaskComplexity.CRITICAL: "claude-3-5-sonnet-20241022",
    },
    "gemini": {
        TaskComplexity.LOW:      "gemini-2.0-flash",
        TaskComplexity.MEDIUM:   "gemini-2.0-flash",
        TaskComplexity.HIGH:     "gemini-2.0-flash",
        TaskComplexity.CRITICAL: "gemini-2.0-flash",
    },
    "nvidia": {
        TaskComplexity.LOW:      "qwen/qwen3.5-397b-a17b",
        TaskComplexity.MEDIUM:   "qwen/qwen3.5-397b-a17b",
        TaskComplexity.HIGH:     "qwen/qwen3.5-397b-a17b",
        TaskComplexity.CRITICAL: "qwen/qwen3.5-397b-a17b",
    },
    "moonshot": {
        TaskComplexity.LOW:      "moonshot-v1-8k",
        TaskComplexity.MEDIUM:   "moonshot-v1-8k",
        TaskComplexity.HIGH:     "moonshot-v1-32k",
        TaskComplexity.CRITICAL: "moonshot-v1-32k",
    },
    "deepseek": {
        TaskComplexity.LOW:      "deepseek-chat",
        TaskComplexity.MEDIUM:   "deepseek-chat",
        TaskComplexity.HIGH:     "deepseek-coder",
        TaskComplexity.CRITICAL: "deepseek-coder",
    },
}

# ── Karmaşıklık Tetikleyicileri ──────────────────────────────
_CRITICAL_KEYWORDS: frozenset[str] = frozenset({
    "security", "güvenlik", "authentication", "authorization", "jwt",
    "sql injection", "xss", "csrf", "encryption", "şifreleme",
    "race condition", "deadlock", "concurrency", "eşzamanlılık",
    "architecture", "mimari", "self-repair", "self-improvement",
    "production", "kritik", "critical", "emergency", "acil",
    "data loss", "veri kaybı", "rollback", "migration",
})

_HIGH_KEYWORDS: frozenset[str] = frozenset({
    "root cause", "kök neden", "debug", "hata analizi",
    "performance", "performans", "optimization", "ölçeklendirme",
    "database schema", "veritabanı şema", "api design", "api tasarımı",
    "refactor", "yeniden yaz", "rewrite", "tech debt",
    "algorithm", "algoritma", "complexity", "karmaşıklık",
    "memory leak", "hafıza sızıntısı",
})

_LOW_PATTERNS: list[str] = [
    r"\bcomment\b", r"\byorum\b", r"\btypo\b",
    r"\bformat\b", r"\bindent\b", r"\bwhitespace\b",
    r"\breadme\b", r"\bdocstring\b", r"\bdoc\b",
    r"\brename\b", r"\byeniden adlandır\b",
    r"\bbasit\b", r"\bsimple\b", r"\beasy\b",
]

# ── Rol -> Varsayılan Karmaşıklık ─────────────────────────────
_ROLE_BASE_COMPLEXITY: dict[str, TaskComplexity] = {
    "architect":    TaskComplexity.HIGH,
    "security":     TaskComplexity.CRITICAL,
    "backend_dev":  TaskComplexity.MEDIUM,
    "frontend_dev": TaskComplexity.MEDIUM,
    "qa_engineer":  TaskComplexity.MEDIUM,
    "devops":       TaskComplexity.MEDIUM,
    "data_eng":     TaskComplexity.MEDIUM,
    "tech_writer":  TaskComplexity.LOW,
    "general":      TaskComplexity.MEDIUM,
}


@dataclass
class RoutingDecision:
    complexity:       TaskComplexity
    provider:         str           # "openai" | "anthropic" | "gemini"
    model:            str           # model string
    reason:           str           # neden bu karar
    estimated_cost_x: float         # relative cost multiplier (1.0 = base)

    def to_dict(self) -> dict:
        return {
            "complexity":       self.complexity.value,
            "provider":         self.provider,
            "model":            self.model,
            "reason":           self.reason,
            "estimated_cost_x": self.estimated_cost_x,
        }


class ModelRouter:
    """
    Prompt + rol + context -> RoutingDecision

    Entegrasyon:
        router = get_model_router()
        decision = router.route(prompt, agent_role="backend_dev")
        # -> decision.provider, decision.model kullan
    """

    def __init__(self, default_provider: str = "anthropic"):
        self.default_provider = default_provider
        self._routing_log: list[dict] = []

    def route(
        self,
        prompt:      str,
        agent_role:  str         = "general",
        task_type:   Optional[str] = None,   # "repair" | "codegen" | "review" | None
        force_complexity: Optional[TaskComplexity] = None,
    ) -> RoutingDecision:
        """Prompt ve bağlama göre routing kararı ver."""
        complexity = force_complexity or self._assess_complexity(prompt, agent_role, task_type)
        provider   = self._select_provider(complexity, agent_role)
        model      = _MODEL_MAP.get(provider, {}).get(complexity, "")

        # Fallback: provider'da bu complexity için model yoksa default al
        if not model:
            model = _MODEL_MAP.get(self.default_provider, {}).get(TaskComplexity.MEDIUM, "unknown")
            provider = self.default_provider

        cost_x = self._cost_multiplier(complexity)
        reason = self._explain(complexity, prompt, agent_role, task_type)

        decision = RoutingDecision(
            complexity=complexity,
            provider=provider,
            model=model,
            reason=reason,
            estimated_cost_x=cost_x,
        )
        self._routing_log.append(decision.to_dict())
        if len(self._routing_log) > 500:
            self._routing_log = self._routing_log[-500:]

        _log.debug(
            f"Routing kararı: {agent_role} -> {provider}/{model} "
            f"[{complexity.value}] | {reason}"
        )
        # Background persistence
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._persist_log(decision, agent_role, prompt[:100]))
        except RuntimeError:
            # aktif loop yoksa persistence atlanır; routing kararı yine döner
            pass
        return decision

    async def _persist_log(self, decision: RoutingDecision, role: str, snippet: str) -> None:
        """Kalıcı veri tabanına yaz."""
        from config import APP_ENV
        if APP_ENV == "test":
            return
        try:
            from db.session import AsyncSessionLocal, is_db_available
            db_ok = await is_db_available()
            if not db_ok:
                return
            from db.models import ModelRouterLog
            async with AsyncSessionLocal() as db:
                log = ModelRouterLog(
                    prompt_snippet   = snippet,
                    agent_role       = role,
                    complexity       = decision.complexity.value,
                    provider         = decision.provider,
                    model            = decision.model,
                    estimated_cost_x = decision.estimated_cost_x,
                    reason           = decision.reason[:500],
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            _log.debug(f"Routing DB save error: {e}")

    def _assess_complexity(self, prompt: str, role: str, task_type: Optional[str]) -> TaskComplexity:
        """Karmaşıklığı belirle."""
        text = prompt.lower()

        # Task type override
        if task_type == "repair":
            return TaskComplexity.HIGH
        if task_type == "security_review":
            return TaskComplexity.CRITICAL

        # Critical keywords
        if any(kw in text for kw in _CRITICAL_KEYWORDS):
            return TaskComplexity.CRITICAL

        # High keywords
        if any(kw in text for kw in _HIGH_KEYWORDS):
            return TaskComplexity.HIGH

        # Uzun prompt -> daha fazla analiz gerekiyor
        if len(prompt) >= 6000:
            return TaskComplexity.HIGH
        if len(prompt) > 2500:
            # Role base ile combine
            role_base = _ROLE_BASE_COMPLEXITY.get(role, TaskComplexity.MEDIUM)
            if role_base == TaskComplexity.HIGH:
                return TaskComplexity.HIGH
            return TaskComplexity.MEDIUM

        # Low pattern kontrolü
        if any(re.search(p, text) for p in _LOW_PATTERNS):
            return TaskComplexity.LOW

        # Default: role bazlı
        return _ROLE_BASE_COMPLEXITY.get(role, TaskComplexity.MEDIUM)

    def _select_provider(self, complexity: TaskComplexity, role: str) -> str:
        """Complexity ve role göre en uygun sağlayıcıyı seç."""
        # Critical / High -> NVIDIA (CHAMPION) > Anthropic öncelikli
        if complexity in (TaskComplexity.CRITICAL, TaskComplexity.HIGH):
            return "nvidia" # New champion model

        # Medium -> Gemini (maliyet/performans dengesi)
        if complexity == TaskComplexity.MEDIUM:
            if role in ("qa_engineer", "data_eng"):
                return "gemini"
            return "openai"

        # Low -> En ucuz
        return "openai"   # gpt-4o-mini

    @staticmethod
    def _cost_multiplier(complexity: TaskComplexity) -> float:
        return {
            TaskComplexity.LOW:      0.05,
            TaskComplexity.MEDIUM:   0.25,
            TaskComplexity.HIGH:     1.0,
            TaskComplexity.CRITICAL: 1.5,
        }[complexity]

    @staticmethod
    def _explain(complexity: TaskComplexity, prompt: str, role: str, task_type: Optional[str]) -> str:
        text = prompt.lower()
        if task_type:
            return f"task_type={task_type}"
        if any(kw in text for kw in _CRITICAL_KEYWORDS):
            kw = next(kw for kw in _CRITICAL_KEYWORDS if kw in text)
            return f"kritik anahtar kelime: '{kw}'"
        if any(kw in text for kw in _HIGH_KEYWORDS):
            kw = next(kw for kw in _HIGH_KEYWORDS if kw in text)
            return f"yüksek karmaşıklık: '{kw}'"
        if len(prompt) > 2500:
            return f"uzun prompt: {len(prompt)} karakter"
        return f"rol bazlı: {role} -> {complexity.value}"

    def stats(self) -> dict:
        """Routing istatistikleri (Performans için şimdilik in-memory log kullanır)."""
        if not self._routing_log:
            return {"total": 0, "complexities": {}, "providers": {}, "avg_cost_x": 0.0}
            
        from collections import Counter
        try:
            # Bellekteki son 500 kaydın özetini çıkar
            complexities = Counter(r.get("complexity", "unknown") for r in self._routing_log)
            providers    = Counter(r.get("provider", "unknown")   for r in self._routing_log)
            total_cost   = sum(r.get("estimated_cost_x", 0.0) for r in self._routing_log)
            count        = len(self._routing_log)
            
            res = {
                "total":        count,
                "complexities": dict(complexities),
                "providers":    dict(providers),
                "avg_cost_x":   round(total_cost / count, 3) if count > 0 else 0.0,
            }
            return res
        except Exception as e:
            return {"total": 0, "error": str(e)}

    def reset_log(self) -> None:
        self._routing_log.clear()


# Singleton
_model_router: "ModelRouter | None" = None


def get_model_router(default_provider: str = "anthropic") -> ModelRouter:
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter(default_provider=default_provider)
    return _model_router
