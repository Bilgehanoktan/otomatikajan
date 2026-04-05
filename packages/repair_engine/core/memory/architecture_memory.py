"""
Architecture Memory — Sistemin resmi mimari kuralları ve sözleşmeleri.

Tutulan bilgiler:
- Canonical contract'lar (Task, Orchestrator, Report, State Transition)
- Module ownership map
- Forbidden patterns
- Layer boundaries
- ADR (Architecture Decision Records)
- Patch safety rules

Bu hafıza olmadan self-repair katmanı yanlış dosyayı düzeltir.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModuleContract:
    """Bir modülün public sözleşmesi."""
    module:          str
    owner_file:      str
    public_symbols:  list[str]    # dışarıya açık fonksiyon/sınıf adları
    dependencies:    list[str]    # import ettiği modüller
    consumers:       list[str]    # bu modülü kullanan modüller
    critical:        bool = False  # True = değiştirirken çok dikkatli ol


@dataclass
class ForbiddenPattern:
    """Kod tabanında yasak olan pattern."""
    pattern:     str
    reason:      str
    replacement: str = ""


@dataclass
class ADR:
    """Architecture Decision Record."""
    id:        str
    title:     str
    status:    str    # accepted | deprecated | superseded
    context:   str
    decision:  str
    rationale: str


class ArchitectureMemory:
    """
    Sistemin mimari hafızası.
    Patch planner ve reviewer bu hafızayı kullanarak
    sözleşme ihlallerini önler.
    """

    def __init__(self):
        self._contracts:  dict[str, ModuleContract] = {}
        self._forbidden:  list[ForbiddenPattern]    = []
        self._adrs:       list[ADR]                 = []
        self._layer_rules: dict[str, list[str]]     = {}   # katman -> bağımlı olabilecekler
        self._patch_safety_rules: list[str]         = []

        # Sistemin canonical kurallarını yükle
        self._load_defaults()

    def _load_defaults(self):
        """Bu projenin canonical mimari kuralları."""

        # ── Canonical Module Contracts ─────────────────────
        contracts = [
            ModuleContract(
                module="core.orchestrator",
                owner_file="core/orchestrator.py",
                public_symbols=["Orchestrator", "ProjectTask", "SubTask", "TaskStatus", "run_project"],
                dependencies=["agents.agent_registry", "llm.model_orchestrator", "quality.scorer"],
                consumers=["main", "api.routes", "core.job_queue", "core.heal_engine"],
                critical=True,
            ),
            ModuleContract(
                module="auth.jwt_auth",
                owner_file="auth/jwt_auth.py",
                public_symbols=["get_current_user", "require_admin", "create_access_token", "JWT_SECRET"],
                dependencies=["db.models", "db.session"],
                consumers=["api.*", "main"],
                critical=True,
            ),
            ModuleContract(
                module="llm.model_orchestrator",
                owner_file="llm/model_orchestrator.py",
                public_symbols=["ModelOrchestrator", "complete", "complete_task", "provider_stats"],
                dependencies=[],
                consumers=["core.orchestrator", "quality.reviewer", "repair.*"],
                critical=True,
            ),
            ModuleContract(
                module="core.job_queue",
                owner_file="core/job_queue.py",
                public_symbols=["JobQueue", "job_queue", "enqueue", "get_job", "list_jobs"],
                dependencies=[],
                consumers=["main", "api.routes", "telegram.bot"],
                critical=True,
            ),
            ModuleContract(
                module="db.session",
                owner_file="db/session.py",
                public_symbols=["AsyncSessionLocal", "init_db", "is_db_available", "get_db_dep"],
                dependencies=[],
                consumers=["db.repository", "api.*", "main"],
                critical=True,
            ),
            ModuleContract(
                module="core.heal_engine",
                owner_file="core/heal_engine.py",
                public_symbols=["SelfHealEngine", "monitor_loop", "system_health_score", "on_subtask_error", "on_subtask_success"],
                dependencies=["heal.*", "core.orchestrator"],
                consumers=["main"],
                critical=False,
            ),
        ]
        for c in contracts:
            self._contracts[c.module] = c

        # ── Forbidden Patterns ─────────────────────────────
        self._forbidden = [
            ForbiddenPattern(
                pattern="from main import",
                reason="Circular import riski — main.py her şeyi import eder",
                replacement="Lazy import kullan: from main import x içinde değil, fonksiyon içinde import et",
            ),
            ForbiddenPattern(
                pattern="except:\\s*pass",
                reason="Sessiz hata yutma — debug edilemez",
                replacement="except Exception as e: logger.warning(...) kullan",
            ),
            ForbiddenPattern(
                pattern="import \\*",
                reason="Wildcard import — isim çakışması ve kaynak belirsizliği",
                replacement="Açık import: from module import SpecificClass",
            ),
            ForbiddenPattern(
                pattern="print\\(",
                reason="Production kodunda print yasak",
                replacement="logger.info() / logger.debug() kullan",
            ),
            ForbiddenPattern(
                pattern="os\\.getenv\\(['\"][A-Z_]+['\"]\\)(?! *,)",
                reason="Varsayılan değer olmadan getenv — production'da None patlayabilir",
                replacement='os.getenv("KEY", "default") veya config.py üzerinden al',
            ),
            ForbiddenPattern(
                pattern="eval\\(|exec\\(",
                reason="Güvenlik açığı — keyfi kod çalıştırma",
                replacement="Hiçbir şeyle değiştirme, tasarımı yeniden düşün",
            ),
            ForbiddenPattern(
                pattern="shell=True",
                reason="Komut enjeksiyonu riski",
                replacement="shell=False ile liste argümanları kullan",
            ),
        ]

        # ── Layer Boundaries ───────────────────────────────
        # Hangi katman hangi katmana bağımlı olabilir
        self._layer_rules = {
            "api":      ["core", "db", "auth", "observability"],
            "core":     ["db", "agents", "llm", "memory", "quality", "heal", "observability"],
            "agents":   ["llm", "observability"],
            "db":       ["observability"],
            "heal":     ["observability"],
            "llm":      ["observability"],
            "repair":   ["core", "db", "llm", "observability"],
            # repair -> auth YASAK (güvenlik modülü)
        }

        # ── Patch Safety Rules ─────────────────────────────
        self._patch_safety_rules = [
            "auth/ altındaki dosyalar değiştirilmeden önce insan onayı alınmalı",
            "db/models.py değişikliği alembic migration gerektirir",
            "core/orchestrator.py public metodları değiştirilirken tüm consumer'lar kontrol edilmeli",
            "main.py router kaydı değiştirilirken integration test koşulmalı",
            "llm/model_orchestrator.py complete() imzası değiştirilmemelidir",
            "JWT_SECRET ve ADMIN_SECRET asla loglanmamalı veya response'a eklenmemeli",
            "Yeni endpoint eklendiyse rate_limiter konfigürasyonu güncellenmeli",
            "ROUTING_POLICY değişikliği agent fallback davranışını etkiler",
        ]

        # ── ADR'ler ────────────────────────────────────────
        self._adrs = [
            ADR(
                id="ADR-001",
                title="LLM çağrıları ModelOrchestrator üzerinden yapılır",
                status="accepted",
                context="Birden fazla LLM provider var, fallback zinciri gerekiyor",
                decision="Tüm LLM çağrıları llm/model_orchestrator.py::ModelOrchestrator.complete() üzerinden geçer",
                rationale="Circuit breaker, fallback ve metrics tek noktada yönetilir",
            ),
            ADR(
                id="ADR-002",
                title="API route'ları read/write/control olarak ayrıştırılmıştır",
                status="accepted",
                context="Tek büyük router bakım zorluğu üretiyor",
                decision="task_read_router / task_write_router / task_control_router ayrımı",
                rationale="Single Responsibility, bağımsız test edilebilirlik",
            ),
            ADR(
                id="ADR-003",
                title="Self-repair modülü production dosyalarına doğrudan yazamaz",
                status="accepted",
                context="Otonom yazma kontrolsüz davranışa yol açabilir",
                decision="Tüm patch önerileri PR olarak sunulur, auto-merge kapalıdır",
                rationale="İnsan onayı zorunludur, sandbox önce, production sonra",
            ),
        ]

    # ── Sorgulama ─────────────────────────────────────────
    def get_contract(self, module: str) -> Optional[ModuleContract]:
        return self._contracts.get(module)

    def is_critical_module(self, filepath: str) -> bool:
        """Bu dosya kritik bir modülün parçası mı?"""
        for contract in self._contracts.values():
            if contract.critical and filepath.startswith(contract.owner_file.split("/")[0]):
                return True
        return False

    def get_forbidden_patterns(self) -> list[ForbiddenPattern]:
        return self._forbidden

    def get_layer_deps(self, layer: str) -> list[str]:
        """Bu katmanın bağımlı olabileceği katmanlar."""
        return self._layer_rules.get(layer, [])

    def check_layer_violation(self, from_module: str, to_module: str) -> Optional[str]:
        """İki modül arasında layer ihlali var mı?"""
        from_layer = from_module.split(".")[0] if "." in from_module else from_module.split("/")[0]
        to_layer   = to_module.split(".")[0]   if "." in to_module   else to_module.split("/")[0]
        allowed    = self._layer_rules.get(from_layer, [])
        if to_layer not in allowed and from_layer != to_layer:
            return f"Layer ihlali: {from_layer} -> {to_layer} bağımlılığı izin verilmiyor."
        return None

    def get_patch_safety_rules(self) -> list[str]:
        return self._patch_safety_rules

    def get_adrs(self) -> list[ADR]:
        return self._adrs

    def consumers_of(self, module: str) -> list[str]:
        """Bu modülü kullanan modüller."""
        contract = self._contracts.get(module)
        return contract.consumers if contract else []

    def to_context_string(self) -> str:
        """LLM için okunabilir mimari bağlam."""
        lines = ["=== MİMARİ HAFIZA ===\n"]
        lines.append("CANONICAL CONTRACTS:")
        for c in self._contracts.values():
            flag = " [KRİTİK]" if c.critical else ""
            lines.append(f"  {c.module}{flag} -> {c.owner_file}")
            lines.append(f"    Public: {', '.join(c.public_symbols[:5])}")

        lines.append("\nFORBIDDEN PATTERNS:")
        for fp in self._forbidden:
            lines.append(f"  YASAK: {fp.pattern[:60]} ({fp.reason[:60]})")

        lines.append("\nPATCH SAFETY RULES:")
        for rule in self._patch_safety_rules:
            lines.append(f"  • {rule}")

        lines.append("\nACTIVE ADRs:")
        for adr in self._adrs:
            if adr.status == "accepted":
                lines.append(f"  [{adr.id}] {adr.title}")

        return "\n".join(lines)


# Singleton
architecture_memory = ArchitectureMemory()
