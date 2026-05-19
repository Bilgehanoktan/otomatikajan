"""
PostgreSQL Veritabanı Modelleri — Faz 2
Kalıcı görev/alt-görev takibi, LLM maliyet logu,
ajan sağlık geçmişi, webhook abonelikleri.
pgvector bağımlılığı opsiyonel — yoksa Memory modeli devre dışı.
"""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import backref, relationship

try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_AVAILABLE = True
except ImportError:
    Vector = None
    _VECTOR_AVAILABLE = False

from libs.db.base import GUID, Base, SmartJSON, utcnow


class ProjectStatus(str, enum.Enum):
    PENDING          = "PENDING"
    QUEUED           = "QUEUED"
    RUNNING          = "RUNNING"
    WAITING          = "WAITING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    REPLAYING        = "REPLAYING"
    RETRYING         = "RETRYING"
    COMPLETED        = "COMPLETED"
    PARTIAL_COMPLETE = "PARTIAL_COMPLETE"
    ERROR            = "ERROR"
    FAILED           = "FAILED"
    CANCELLED        = "CANCELLED"
    PAUSED           = "PAUSED"
    INTERRUPTED      = "INTERRUPTED"
    RESUMING         = "RESUMING"
    PENDING_APPROVAL_AUTO = "PENDING_APPROVAL_AUTO"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup automatically."""
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None

class ProjectSource(str, enum.Enum):
    API = "API"
    MANUAL = "MANUAL"
    TELEGRAM = "TELEGRAM"
    SCHEDULED = "SCHEDULED"
    QUEUE_STUCK = "QUEUE_STUCK"
    APPROVAL_TIMEOUT = "APPROVAL_TIMEOUT"
    CONTROL_PLANE = "CONTROL_PLANE"
    CEO = "CEO"

    @classmethod
    def _missing_(cls, value):
        """Ultra-Resilient Lookup for Source (Case-Insensitive)."""
        if not isinstance(value, str):
            return None
        val = value.upper().strip()
        for member in cls:
            if member.value.upper() == val:
                return member
        return None

class TaskPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"

    @classmethod
    def _missing_(cls, value):
        """
        Ultra-Resilient Lookup Handler (Phase 4 Hardening).
        Supports:
        - Turkish (KRİTİK, YÜKSEK, ORTA, DÜŞÜK)
        - Turkish ASCII (KRITIK, YUKSEK, DUSUK)
        - English (CRITICAL, HIGH, MEDIUM, LOW)
        - All casing permutations (yüksek, Medium, etc.)
        """
        if not isinstance(value, str):
            return None

        # Normalize: Upper and mapping
        val = value.upper().strip()

        # Explicit Mapping Table
        mapping = {
            # Turkish variants
            "KRİTİK": "CRITICAL",
            "KRITIK": "CRITICAL",
            "YÜKSEK": "HIGH",
            "YUKSEK": "HIGH",
            "ORTA":   "MEDIUM",
            "DÜŞÜK":  "LOW",
            "DUSUK":  "LOW",
            # English aliases
            "MEDIUM": "MEDIUM",
            "NORMAL": "MEDIUM",
            "URGENT": "CRITICAL",
        }

        target = mapping.get(val, val)

        # Check by member value
        for member in cls:
            if member.value == target:
                return member
        # Check by member name
        try:
            return cls[target]
        except KeyError:
            return None

# ── Soft CEO: Domain Enums ────────────────────────────────
class SoftCeoDecisionType(str, enum.Enum):
    """Soft CEO ajanının üretebileceği karar tipleri."""
    AUTO_APPROVE_CANDIDATE  = "AUTO_APPROVE_CANDIDATE"
    AUTO_REPLAY_CANDIDATE   = "AUTO_REPLAY_CANDIDATE"
    REQUIRES_PRIME_REVIEW   = "REQUIRES_PRIME_REVIEW"
    REQUIRES_QUORUM         = "REQUIRES_QUORUM"
    REQUIRES_HUMAN_CONTEXT  = "REQUIRES_HUMAN_CONTEXT"
    ARCHIVE_STALE           = "ARCHIVE_STALE"
    NO_ACTION               = "NO_ACTION"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None


class SoftCeoRiskClass(str, enum.Enum):
    """Soft CEO risk sınıflandırması."""
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None


class PendingReason(str, enum.Enum):
    """Bir iş kaleminin neden beklediğini tanımlayan sınıflandırma."""
    PENDING_APPROVAL   = "PENDING_APPROVAL"
    SAFETY_LOCK        = "SAFETY_LOCK"
    OPEN_INCIDENT      = "OPEN_INCIDENT"
    PAUSED_WORKFLOW    = "PAUSED_WORKFLOW"
    MISSING_CONTEXT    = "MISSING_CONTEXT"
    STALE_QUEUE_ITEM   = "STALE_QUEUE_ITEM"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None

# ── Faz 12: Fleet Orchestra Enums ─────────────────────────
class FleetStatus(str, enum.Enum):
    ACTIVE   = "ACTIVE"
    DEGRADED = "DEGRADED"
    FROZEN   = "FROZEN"
    DRAINING = "DRAINING"
    FAILED   = "FAILED"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None

class AgentStatus(str, enum.Enum):
    IDLE        = "IDLE"
    ASSIGNED    = "ASSIGNED"
    BUSY        = "BUSY"
    PAUSED      = "PAUSED"
    QUARANTINED = "QUARANTINED"
    OFFLINE     = "OFFLINE"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None

class AgentRole(str, enum.Enum):
    PLANNER     = "PLANNER"
    EXECUTOR    = "EXECUTOR"
    REVIEWER    = "REVIEWER"
    REPAIRER    = "REPAIRER"
    GOVERNOR    = "GOVERNOR"
    AUDITOR     = "AUDITOR"
    SYNTHESIZER = "SYNTHESIZER"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None


# ── Projeler ─────────────────────────────────────────────
class Project(Base):
    __tablename__ = "projects"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    owner_id     = Column(GUID, ForeignKey("operators.id", ondelete="SET NULL"), nullable=True)
    title        = Column(String(500), nullable=False)
    description  = Column(Text, default="")
    status       = Column(SAEnum(ProjectStatus, native_enum=False, length=32), default=ProjectStatus.PENDING, nullable=False, index=True)
    report       = Column(Text, default="")
    job_id       = Column(String(64), nullable=True, index=True)   # Celery task ID
    total_cost   = Column(Float, default=0.0)
    budget_limit = Column(Float, default=0.0)            # 0.0 = unlimited
    # ── Faz 4: Task Tracking alanları ─────────────────────
    source        = Column(SAEnum(ProjectSource, native_enum=False, length=32), default=ProjectSource.API, nullable=False, index=True)
    # source: "api" | "manual" | "telegram" | "scheduled"
    priority      = Column(SAEnum(TaskPriority, native_enum=False, length=16), default=TaskPriority.MEDIUM, nullable=False, index=True)
    # priority: "critical" | "high" | "medium" | "low"
    priority_level = Column(Integer, default=50)           # 1-100 (for CEO engine)
    progress_pct  = Column(Integer, default=0)           # 0-100
    tags          = Column(SmartJSON(), default=list)           # ["tag1", "tag2"]
    deadline      = Column(DateTime(timezone=True), nullable=True)
    assigned_agent= Column(String(64), default="")       # preferred agent
    error_detail  = Column(Text, default="")             # son hata detayı
    retry_count   = Column(Integer, default=0)
    notes         = Column(Text, default="")             # yönetici notları
    cancelled_at  = Column(DateTime(timezone=True), nullable=True)
    cancelled_by  = Column(String(128), default="")
    workflow_template = Column(String(32), default="default", nullable=False, index=True)
    quality_profile   = Column(String(32), default="standard", nullable=False, index=True)
    acceptance_criteria = Column(SmartJSON(), default=list)
    execution_context   = Column(SmartJSON(), default=dict)
    review_required     = Column(Boolean, default=False, nullable=False)
    checkpoint_data     = Column(SmartJSON(), default=dict)  # AGI Dayanıklılık: Son güvenli durum verisi
    goal_id             = Column(GUID, ForeignKey("sovereign_goals.id", ondelete="SET NULL"), nullable=True)
    ceo_managed         = Column(Boolean, default=False, index=True)

    # ── Faz 23: Multi-Project Fleet & Isolation ──
    isolation_tier      = Column(Integer, default=2, nullable=False, index=True)
    # 0: Mission Critical, 1: Production, 2: Standard, 3: Sandbox/Trial
    autonomy_envelope   = Column(SmartJSON(), default={
        "mode": "advisory",           # advisory, autonomous, human_in_loop
        "allow_auto_patch": False,
        "max_risk_score": 0.3,
        "isolation_zone": "global"    # global, restricted_to_region
    })
    concurrency_limit   = Column(Integer, default=5, nullable=False)
    # ── Faz 24: Predictive Fleet Economics ──
    current_budget_usd  = Column(Float, default=0.0)
    hourly_burn_rate    = Column(Float, default=0.0)
    economic_profile    = Column(SmartJSON(), default={
        "steering_policy": "cost_optimized", # cost_optimized, performance_optimized, balanced
        "min_budget_threshold": 10.0,       # Alert threshold in USD
        "auto_scale_concurrency": True      # Adaptive Quota Balancing trigger
    })

    metadata_           = Column(SmartJSON(), default=dict)
    # ──────────────────────────────────────────────────────
    is_pilot     = Column(Boolean, default=False, nullable=False, index=True)
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at   = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    started_at   = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    owner    = relationship("Operator", backref="projects")
    subtasks = relationship("SubTask", back_populates="project",
                            lazy="select", cascade="all, delete-orphan")
    cost_logs= relationship("LLMCostLog", back_populates="project",
                            lazy="select", cascade="all, delete-orphan")
    task_logs= relationship("TaskLog", back_populates="project",
                            lazy="select", cascade="all, delete-orphan")
    goal     = relationship("SovereignGoal", back_populates="projects", foreign_keys=[goal_id])
    workflow_events = relationship("WorkflowEvent", back_populates="project",
                                   lazy="select", cascade="all, delete-orphan")


# ── Alt Görevler ─────────────────────────────────────────
class SubTask(Base):
    __tablename__ = "subtasks"

    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id    = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"))
    agent_id      = Column(String(64), nullable=False, index=True)
    action        = Column(String(128), default="run_agent", nullable=False)
    prompt        = Column(Text, nullable=False)
    result        = Column(Text, default="")
    status        = Column(SAEnum(ProjectStatus, native_enum=False, length=32), default=ProjectStatus.PENDING, nullable=False, index=True)
    attempts      = Column(Integer, default=0)
    recovered     = Column(Boolean, default=False)   # heal engine kurtardı mı?
    llm_provider  = Column(String(64), default="")
    input_tokens  = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd      = Column(Float, default=0.0)
    latency_s     = Column(Float, default=0.0)
    quality_score = Column(Float, nullable=True)
    quality_detail = Column(SmartJSON(), default=dict)
    input_data     = Column(SmartJSON(), default=dict)
    input_schema   = Column(SmartJSON(), default=dict)
    internal_monologue = Column(Text, default="")
    reviewed      = Column(Boolean, default=False, nullable=False)
    review_notes  = Column(SmartJSON(), default=list)
    causal_anchor = Column(Text, default="")         # Faz 12.3: Bu adımın ana çıkarımı (Anchor)
    inhibition_signals = Column(SmartJSON(), default=list) # Faz 12.3: Negatif sinapslar / Kısıtlar
    parent_id     = Column(GUID, ForeignKey("subtasks.id"), nullable=True)
    dependencies  = Column(SmartJSON(), default=list)
    created_at    = Column(DateTime(timezone=True), default=utcnow)

    updated_at    = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    completed_at  = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="subtasks")

    @property
    def result_summary(self) -> str:
        """Truncated version of result for UI list views."""
        if not self.result:
            return ""
        return self.result[:200] + ("..." if len(self.result) > 200 else "")


# ── LLM Maliyet Logu ─────────────────────────────────────
class LLMCostLog(Base):
    __tablename__ = "llm_cost_logs"

    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id    = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    provider      = Column(String(64), nullable=False, index=True)
    model         = Column(String(128), nullable=False)
    agent_id      = Column(String(64), nullable=False)
    input_tokens  = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd      = Column(Float, default=0.0, nullable=False)
    latency_s     = Column(Float, default=0.0)
    success       = Column(Boolean, default=True)
    error_type    = Column(String(64), default="")
    agent_role    = Column(String(50), index=True)
    created_at    = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project = relationship("Project", back_populates="cost_logs")


# ── Domain Event Logu (audit trail) ──────────────────────
class DomainEventLog(Base):
    __tablename__ = "domain_event_logs"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    event_type = Column(String(128), nullable=False, index=True)
    agent_id   = Column(String(64), default="system")
    severity   = Column(String(32), default="info")
    phase      = Column(String(32), default="")
    message    = Column(Text, default="")
    payload    = Column(SmartJSON(), default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


# ── Ajan Sağlık Geçmişi ──────────────────────────────────
class AgentHealthLog(Base):
    __tablename__ = "agent_health_logs"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    agent_id   = Column(String(64), nullable=False, index=True)
    score      = Column(Float, nullable=False)
    state      = Column(String(32), default="healthy")
    severity   = Column(String(32), default="info")
    message    = Column(Text, default="")
    action     = Column(String(64), default="")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


# ── AGI Stratejik Hedefler (Faz 79) ──────────────────────
class SovereignGoal(Base):
    """
    Sistemin North Star (Kutup Yıldızı) Hedefleri. 
    Aylar sürecek 'Ana Vizyon' ve 'Stratejik Yol Haritası' burada tutulur.
    """
    __tablename__ = "sovereign_goals"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    title            = Column(String(512), nullable=False)
    vision_statement = Column(Text, nullable=False)     # "Tam otonom Geliştirici AGI olmak"
    priority         = Column(Integer, default=50)      # 1-100
    status           = Column(String(32), default="active") # active, achieved, pivoted
    kpis             = Column(SmartJSON(), default=dict) # {"cost_per_task": 0.5, "failure_rate": 0.05}
    target_date      = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow)
    achieved_at      = Column(DateTime(timezone=True), nullable=True)
    completed_at     = Column(DateTime(timezone=True), nullable=True) # Alias/Field for CEO Engine

    projects    = relationship("Project", back_populates="goal",
                             primaryjoin="SovereignGoal.id == Project.goal_id",
                             foreign_keys="[Project.goal_id]")
    suggestions = relationship("CEOSuggestedTask", back_populates="goal_ref")


# ── Webhook Abonelikleri ──────────────────────────────────
class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    owner_id   = Column(GUID, ForeignKey("operators.id", ondelete="CASCADE"), nullable=True)
    url        = Column(String(2048), nullable=False)
    events     = Column(SmartJSON(), default=list)
    secret     = Column(String(64), nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    owner = relationship("Operator")


# ── Rate Limit Sayacı (Redis yoksa DB fallback) ───────────
class RateLimitCounter(Base):
    __tablename__ = "rate_limit_counters"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    key        = Column(String(256), unique=True, nullable=False, index=True)
    count      = Column(Integer, default=0)
    window_end = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ── Görev Log Geçmişi (Faz 4) ────────────────────────────
class TaskLog(Base):
    """Her görev durum değişikliği, hata ve önemli olay buraya yazılır."""
    __tablename__ = "task_logs"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    level      = Column(String(16), default="info", nullable=False)
    # level: "debug" | "info" | "warning" | "error" | "critical"
    event      = Column(String(128), nullable=False, index=True)
    # event: "status_change" | "agent_start" | "agent_done" | "retry" | "error" | "cancelled"
    message    = Column(Text, default="")
    agent_id   = Column(String(64), default="system")
    payload    = Column(SmartJSON(), default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project = relationship("Project", back_populates="task_logs")

    __table_args__ = (
        Index("ix_task_logs_project_created", "project_id", "created_at"),
    )


# ── API Metrik Kayıtları (Faz 4 — Monitoring) ────────────
class ApiMetric(Base):
    """
    Her HTTP isteğinin özeti.
    RequestTracingMiddleware tarafından doldurulur.
    Eski kayıtlar periyodik olarak temizlenmelidir (retention: 7 gün).
    """
    __tablename__ = "api_metrics"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    endpoint     = Column(String(256), nullable=False, index=True)
    method       = Column(String(8), nullable=False)
    status_code  = Column(Integer, nullable=False, index=True)
    response_ms  = Column(Float, nullable=False)           # milisaniye
    user_id      = Column(GUID, nullable=True)
    ip_address   = Column(String(64), default="")
    trace_id     = Column(String(32), default="", index=True)
    error_type   = Column(String(128), default="")
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_api_metrics_endpoint_created", "endpoint", "created_at"),
        Index("ix_api_metrics_created", "created_at"),
    )


# ── Workflow Olay Geçmişi (Faz 13.04 — Durable Execution) ──
class WorkflowEvent(Base):
    """
    Temporal-like event history. Her workflow adımı ve durum değişikliği
    burada immutably saklanır. Recovery için bu tablo replay edilir.
    Faz 13.04: Tamper-evident hash chaining ve operator takibi eklendi.
    """
    __tablename__ = "workflow_events"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id   = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True) # Changed to support system-wide events
    event_type   = Column(String(64), nullable=False, index=True)
    # event_type: "workflow_started", "step_scheduled", "step_started",
    #             "step_completed", "step_failed", "context_updated", "workflow_completed",
    #             "manual_approval", "workflow_replayed", "workflow_cancelled"

    step_id      = Column(String(128), nullable=True, index=True)
    operator_id  = Column(String(128), nullable=True, index=True) # "system" veya User.email

    payload      = Column(SmartJSON(), default=dict)

    # ── Tamper-Evidence (Audit Chain) ──
    previous_hash = Column(String(64), nullable=True)             # Bir önceki event'in imzası
    signature     = Column(String(64), nullable=True, index=True) # Bu kaydın özgün özeti (SHA256)

    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project = relationship("Project", back_populates="workflow_events")

    __table_args__ = (
        Index("ix_workflow_events_project_created", "project_id", "created_at"),
    )


# ── Model Router Logları (Faz 12) ───────────────────────────
class ModelRouterLog(Base):
    """
    Model router tarafından verilen her kararın kaydı.
    Dashboard istatistikleri için kullanılır.
    """
    __tablename__ = "model_router_logs"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    prompt_snippet   = Column(String(500), default="")
    agent_role       = Column(String(64), nullable=False, index=True)
    complexity       = Column(String(32), nullable=False, index=True)
    provider         = Column(String(64), nullable=False, index=True)
    model            = Column(String(128), nullable=False)
    estimated_cost_x = Column(Float, default=1.0)
    reason           = Column(String(512), default="")
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_model_router_logs_created", "created_at"),
    )


# ── Telegram Kullanıcıları (Faz 4) ───────────────────────
class TelegramUser(Base):
    """Telegram bot erişim izni verilen kullanıcılar."""
    __tablename__ = "telegram_users"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    telegram_id  = Column(String(32), unique=True, nullable=False, index=True)
    username     = Column(String(128), default="")
    full_name    = Column(String(256), default="")
    is_authorized= Column(Boolean, default=False, nullable=False)
    is_admin     = Column(Boolean, default=False)
    # İlişkili sistem kullanıcısı (opsiyonel)
    user_id      = Column(GUID, ForeignKey("operators.id", ondelete="SET NULL"), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    command_count= Column(Integer, default=0)
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("Operator")


# ── Telegram Komut Logu (Faz 4) ──────────────────────────
class TelegramCommandLog(Base):
    """Telegram'dan gelen tüm komutlar loglanır."""
    __tablename__ = "telegram_command_logs"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    telegram_id  = Column(String(32), nullable=False, index=True)
    command      = Column(String(64), nullable=False)
    arguments    = Column(Text, default="")
    response     = Column(Text, default="")
    success      = Column(Boolean, default=True)
    project_id   = Column(GUID, nullable=True)  # komuttan oluşan görev
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


# ── Bellek / RAG Deposu (memory/store.py için) ───────────
class Memory(Base):
    """Ajan belleği — RAG sistemi için vektör + metin depolama.
    Geliştirilmiş Faz 12 Standardı: DB ile tam uyumluluk (10 kolon).
    """
    __tablename__ = "memories"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    agent_id    = Column(String(64), nullable=False, index=True)
    body        = Column("content", Text, nullable=False)            # DB'de 'content' olarak geçer
    category    = Column(String(64), default="general", nullable=False, index=True)
    importance  = Column(Float, default=0.5, nullable=False)
    metadata_   = Column(SmartJSON(), default=dict)                        # DB'de JSONB
    tags        = Column(SmartJSON(), default=list)                        # DB'de JSONB
    expires_at  = Column(DateTime(timezone=True), nullable=True)
    project_id  = Column(String(64), nullable=True, index=True)      # DB'de 'character varying'
    parent_id   = Column(GUID, ForeignKey("memories.id"), nullable=True, index=True) # Causal Anchoring
    cause_id    = Column(GUID, nullable=True, index=True) # Linked to a specific event or ErrorID
    created_at  = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


# ── CEO Engine Modelleri (Faz 8) ──────────────────────────
class CEOSuggestedTask(Base):
    __tablename__ = "ceo_suggested_tasks"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    opportunity_id   = Column(GUID, ForeignKey("improvement_opportunities.id"))
    title            = Column(String(512), nullable=False)
    description      = Column(Text)
    priority         = Column(String(32), default="medium")
    owner_agent_hint = Column(String(64), default="architect")
    status           = Column(String(32), default="suggested")
    parent_id        = Column(GUID, ForeignKey("ceo_suggested_tasks.id"), nullable=True) # Hiyerarşik planlama
    plan_hierarchy   = Column(SmartJSON(), default=dict) # {"step_index": 1, "total_steps": 3, "depends_on": [...]}
    reasoning_summary= Column(Text)
    impact_projection= Column(SmartJSON(), default=dict)
    created_task_id  = Column(GUID, ForeignKey("projects.id"), nullable=True)
    goal_id          = Column(GUID, ForeignKey("sovereign_goals.id"), nullable=True) # North Star Link
    created_at       = Column(DateTime(timezone=True), default=utcnow)
    updated_at       = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    opportunity = relationship("ImprovementOpportunity", back_populates="suggestions")
    created_task = relationship("Project", backref=backref("suggestion_source", uselist=False), foreign_keys=[created_task_id])
    sub_tasks    = relationship("CEOSuggestedTask", backref=backref("parent", remote_side=[id]))
    goal_ref     = relationship("SovereignGoal", back_populates="suggestions")


class ImprovementOpportunity(Base):
    __tablename__ = "improvement_opportunities"
    __table_args__ = {"extend_existing": True}

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_type      = Column(String(64), nullable=False)   # logs, performance, anomaly
    source_ref       = Column(String(256))
    title            = Column(String(512), nullable=False)
    description      = Column(Text)
    severity         = Column(String(16), default="medium")
    category         = Column(String(64), default="reliability")
    impact_score     = Column(Float, default=0.0)
    urgency_score    = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    effort_score     = Column(Float, default=0.0)
    priority_score   = Column(Float, default=0.0, index=True)
    pattern_hash     = Column(String(64), unique=True)
    evidence_detail  = Column(Text)
    affected_files   = Column(SmartJSON(), default=list) # Phase 12.1: Tracking affected files
    status           = Column(String(32), default="open", index=True) # open, suggested, resolved
    severity_score   = Column(Float, default=0.0)
    impact           = Column(Float, default=0.0)
    created_at       = Column(DateTime(timezone=True), default=utcnow)

    suggestions      = relationship("CEOSuggestedTask", back_populates="opportunity", cascade="all, delete-orphan")

    @staticmethod
    def generate_hash(source_type: str, source_ref: str) -> str:
        import hashlib
        payload = f"{source_type}:{source_ref or ''}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]


class CEODecision(Base):
    __tablename__ = "ceo_decisions"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    opportunity_id   = Column(GUID, ForeignKey("improvement_opportunities.id"))
    decision_type    = Column(String(64)) # suggest_task, auto_approve, ignore
    decision_summary = Column(Text)
    summary          = Column(Text)     # Field for CEO Engine
    context          = Column(SmartJSON(), default=dict) # Field for CEO Engine
    decision_source  = Column(String(64), default="llm")
    applied_at       = Column(DateTime(timezone=True), default=utcnow) # Field for CEO Engine
    created_at       = Column(DateTime(timezone=True), default=utcnow)



class CEOPerformanceLog(Base):
    __tablename__ = "ceo_performance_logs"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    suggestion_id    = Column(GUID, ForeignKey("ceo_suggested_tasks.id"))
    project_id       = Column(GUID, ForeignKey("projects.id"))
    agent_id         = Column(String(64))
    opportunity_type = Column(String(64))
    success          = Column(Boolean, default=True)
    impact_score     = Column(Float, default=0.0)
    final_reasoning  = Column(Text)
    created_at       = Column(DateTime(timezone=True), default=utcnow)


# ── Beceri Yürütme Logları (Faz 14) ────────────────────────
class SkillExecutionLog(Base):
    """Her beceri (skill) çalıştırıldığında buraya kaydedilir."""
    __tablename__ = "skill_execution_logs"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id   = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_id     = Column(String(64), nullable=True, index=True)
    skill_id     = Column(String(64), nullable=False, index=True)
    success      = Column(Boolean, default=True, nullable=False)
    summary      = Column(Text, default="")
    data         = Column(SmartJSON(), default=dict) # Skill-specific output
    duration_s   = Column(Float, default=0.0)
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project = relationship("Project")


# ── Egemen Kod Üretim Modelleri (Faz 12.1 - Sovereign Codegen) ──
class SovereignCodeResult(Base):
    """
    Sovereign AGI tarafından üretilen kod paketlerinin üst verisi.
    Her sonuç bir Proje (Project) ile ilişkilidir.
    """
    __tablename__ = "sovereign_code_results"

    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id     = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title          = Column(String(512), nullable=False)
    language       = Column(String(64), default="mixed")
    technologies   = Column(SmartJSON(), default=list) # ["react", "fastapi"]
    status         = Column(String(32), default="generated") # generating, completed, failed
    summary        = Column(Text, default="")
    total_files    = Column(Integer, default=0)
    provenance_hash= Column(String(64), nullable=True) # ProvenanceEngine entegrasyonu için
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at     = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project = relationship("Project")
    files   = relationship("SovereignCodeFile", back_populates="result", cascade="all, delete-orphan")


class SovereignCodeFile(Base):
    """
    Üretilen her bir dosyanın içeriği ve metadata bilgisi.
    """
    __tablename__ = "sovereign_code_files"

    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    result_id      = Column(GUID, ForeignKey("sovereign_code_results.id", ondelete="CASCADE"), nullable=False, index=True)
    filename       = Column(String(256), nullable=False)
    path           = Column(String(1024), nullable=False)
    content        = Column(Text, nullable=False)
    language       = Column(String(64), default="python")
    is_generated   = Column(Boolean, default=True)
    provenance_id  = Column(String(64), nullable=True) # Her dosya bazlı köken takibi
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    result = relationship("SovereignCodeResult", back_populates="files")


# ── Faz 60+: Sovereign Model Governance & NAS ──────────
class SovereignModelPolicy(Base):
    """
    Her ajan rolü için en iyi çalışan (NASOptimizer tarafından belirlenen)
    model ve fallback zinciri politikasını saklar.
    """
    __tablename__ = "sovereign_model_policies"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    agent_role       = Column(String(64), nullable=False, unique=True, index=True)
    winner_provider  = Column(String(64), nullable=False)
    runner_up        = Column(String(64), nullable=True)
    fallback_chain   = Column(SmartJSON(), default=list) # ["openai", "gemini", ...]
    confidence       = Column(Float, default=0.5)
    last_optimized   = Column(DateTime(timezone=True), default=utcnow)
    created_at       = Column(DateTime(timezone=True), default=utcnow)
    updated_at       = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ModelBenchmarking(Base):
    """
    NAS (Neural Architecture Search) için modellerin tarihsel performans metrikleri.
    """
    __tablename__ = "model_benchmarking"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    agent_role       = Column(String(64), nullable=False, index=True)
    provider         = Column(String(64), nullable=False, index=True)
    avg_latency      = Column(Float, default=0.0)
    avg_cost         = Column(Float, default=0.0)
    success_rate     = Column(Float, default=0.0)
    quality_score    = Column(Float, default=0.0)
    recorded_at      = Column(DateTime(timezone=True), default=utcnow, index=True)


# ── Öz-İyileştirme Yamaları (Faz 4) ────────────────────────
class SystemImprovement(Base):
    """
    Otonom olarak üretilen sistem dÃ¼zeltmeleri (patches).
    """
    __tablename__ = "system_improvements"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    opportunity_id   = Column(GUID, ForeignKey("improvement_opportunities.id"), nullable=True)
    target_file      = Column(String(512), nullable=False)
    instruction      = Column(Text, nullable=False)
    proposed_patch   = Column(Text, nullable=False)   # Unified diff or full file
    risk_score       = Column(Float, default=0.0)
    test_results     = Column(SmartJSON(), default=dict) # Shadow runner output
    status           = Column(String(32), default="pending", index=True) # pending, verified, applied, rejected
    applied_at       = Column(DateTime(timezone=True), nullable=True)
    git_commit       = Column(String(64), nullable=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow, index=True)

    opportunity = relationship("ImprovementOpportunity")


# ── Faz 14: Operasyonel Yönetişim Modelleri ────────────────
class ApprovalRequest(Base):
    """
    İnsan onayı bekleyen ajan kararları.
    """
    __tablename__ = "approval_requests"

    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id    = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id       = Column(String(128), nullable=True)
    request_type  = Column(String(64), nullable=False) # budget, autonomy, risk_score
    reason        = Column(Text, nullable=False)
    input_data    = Column(SmartJSON(), default=dict) # Neye onay veriliyor?

    status        = Column(String(32), default="pending", index=True) # pending, approved, rejected
    approver_id   = Column(String(128), nullable=True)
    decision_at   = Column(DateTime(timezone=True), nullable=True)
    comment       = Column(Text, default="")

    created_at    = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project = relationship("Project")


class OperationalIncident(Base):
    """
    Sistem tarafından otomatik tespit edilen operasyonel darboğazlar.
    """
    __tablename__ = "operational_incidents"

    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    incident_type = Column(String(64), nullable=False, index=True) # stuck_workflow, budget_breach, safety_violation
    severity      = Column(String(16), default="medium")
    message       = Column(Text, nullable=False)

    status        = Column(String(32), default="open", index=True) # open, investigating, resolved, archived
    project_id    = Column(GUID, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    payload       = Column(SmartJSON(), default=dict)
    resolved_at   = Column(DateTime(timezone=True), nullable=True)
    created_at    = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project = relationship("Project")


class SovereignEvidence(Base):
    """
    Faz 26: R-01 Live Field Evidence Depth.
    Otonom kararların, müdahalelerin ve ekonomik sapmaların doğrulanabilir kanıtları.
    """
    __tablename__ = "sovereign_evidence"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    evidence_type    = Column(String(64), nullable=False, index=True) # self_healing, economic_drift, failover, rollback
    severity         = Column(String(16), default="info")

    project_id       = Column(GUID, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    incident_id      = Column(GUID, ForeignKey("operational_incidents.id", ondelete="SET NULL"), nullable=True)
    improvement_id   = Column(GUID, ForeignKey("system_improvements.id", ondelete="SET NULL"), nullable=True)

    # Derinlemesine Kanıt Verisi: decision_logic, risk_delta, cost_delta, validation_tokens
    payload          = Column(SmartJSON(), default=dict)

    provenance_hash  = Column(String(64), nullable=True) # Değişmezlik doğrulaması
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project    = relationship("Project")
    incident   = relationship("OperationalIncident")
    improvement= relationship("SystemImprovement")


class FederationTrust(Base):
    """
    Faz 26: R-09 Federation Trust Score Depth.
    Küme (cluster) bazlı güven puanları ve otonom kararlılık metrikleri.
    """
    __tablename__ = "federation_trust"

    cluster_id       = Column(String(64), primary_key=True) # e.g., sec-overwatch-v1
    trust_score      = Column(Float, default=1.0)           # 0.0 - 1.0

    # Başarı/Başarısızlık Metrikleri
    success_count    = Column(Integer, default=0)
    failure_count    = Column(Integer, default=0)
    arbitration_wins = Column(Integer, default=0)           # Çelişki çözümleme başarısı

    # Decay Modeli için
    last_activity_at = Column(DateTime(timezone=True), default=utcnow)

    # Metadata: cluster_version, preferred_models, isolation_stats
    cluster_metadata = Column(SmartJSON(), default=dict)

    updated_at       = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class FederationTrustHistory(Base):
    """
    Güven puanı değişim geçmişi (Time-series).
    """
    __tablename__ = "federation_trust_history"

    id               = Column(Integer, primary_key=True)
    cluster_id       = Column(String(64), nullable=False, index=True)
    trust_score      = Column(Float, nullable=False)
    change_reason    = Column(String(256)) # success, failure, decay, arbitration_win

    payload          = Column(SmartJSON(), default=dict) # O anki metrikler
    created_at       = Column(DateTime(timezone=True), default=utcnow, index=True)

# ── Faz 12: Fleet Orchestra Modelleri ─────────────────────

class FleetCluster(Base):
    """Filonun mantıksal veya coğrafi gruplandırılması."""
    __tablename__ = "fleet_clusters"
    __table_args__ = {"extend_existing": True}

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    name            = Column(String(128), nullable=False)
    status          = Column(SAEnum(FleetStatus, native_enum=False, length=32), default=FleetStatus.ACTIVE, index=True)
    region          = Column(String(64), default="global")

    budget_limit    = Column(Float, default=0.0)
    current_budget_usage = Column(Float, default=0.0)
    max_parallel_projects = Column(Integer, default=5)

    created_at      = Column(DateTime(timezone=True), default=utcnow)
    updated_at      = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class AgentNode(Base):
    """Fila içindeki aktif bir ajan düğümü (node)."""
    __tablename__ = "agent_nodes"
    __table_args__ = {"extend_existing": True}

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    cluster_id      = Column(GUID, ForeignKey("fleet_clusters.id", ondelete="SET NULL"), nullable=True)
    name            = Column(String(128), nullable=False)
    role            = Column(SAEnum(AgentRole, native_enum=False, length=32), nullable=False, index=True)
    status          = Column(SAEnum(AgentStatus, native_enum=False, length=32), default=AgentStatus.IDLE, index=True)

    trust_score     = Column(Float, default=1.0)
    success_count   = Column(Integer, default=0)
    failure_count   = Column(Integer, default=0)
    current_load    = Column(Integer, default=0)
    max_concurrency = Column(Integer, default=1)

    last_heartbeat  = Column(DateTime(timezone=True), default=utcnow)
    project_scope   = Column(String(256)) # comma separated or pattern
    cost_rate       = Column(Float, default=0.0) # USD per task or hour

    capabilities    = Column(SmartJSON(), default=dict)

    created_at      = Column(DateTime(timezone=True), default=utcnow)
    updated_at      = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    cluster = relationship("FleetCluster", backref="agents")

class FleetAssignment(Base):
    """Bir ajanın bir projeye atanması."""
    __tablename__ = "fleet_assignments"
    __table_args__ = {"extend_existing": True}

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id      = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    agent_id        = Column(GUID, ForeignKey("agent_nodes.id", ondelete="CASCADE"), index=True)

    assignment_type = Column(String(64), default="primary") # primary, peer, auditor
    status          = Column(String(32), default="active") # active, completed, released

    started_at      = Column(DateTime(timezone=True), default=utcnow)
    ended_at        = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project")
    agent   = relationship("AgentNode")

class ProjectExecutionPlan(Base):
    """Bir projenin filo düzeyindeki yürütme planı."""
    __tablename__ = "project_execution_plans"
    __table_args__ = {"extend_existing": True}

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id      = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    orchestration_mode = Column(String(32), default="standard") # standard, high_risk, fast_track
    required_roles     = Column(SmartJSON(), default=list)      # ["PLANNER", "EXECUTOR", "REVIEWER"]
    estimated_cost     = Column(Float, default=0.0)
    priority_override  = Column(Integer, nullable=True)

    status             = Column(String(32), default="draft")    # draft, allocated, running, completed
    created_at         = Column(DateTime(timezone=True), default=utcnow)

class ProjectAgentAllocation(Base):
    """Proje için ayrılan (reserved) ajan kaynakları."""
    __tablename__ = "project_agent_allocations"
    __table_args__ = {"extend_existing": True}

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id      = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    role            = Column(SAEnum(AgentRole, native_enum=False, length=32), nullable=False)
    count           = Column(Integer, default=1)

    allocated_count = Column(Integer, default=0)
    is_satisfied    = Column(Boolean, default=False)
