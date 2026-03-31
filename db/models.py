"""
PostgreSQL Veritabanı Modelleri — Faz 2
Kalıcı görev/alt-görev takibi, LLM maliyet logu,
ajan sağlık geçmişi, webhook abonelikleri.
pgvector bağımlılığı opsiyonel — yoksa Memory modeli devre dışı.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, Index, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import enum

try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_AVAILABLE = True
except ImportError:
    Vector = None
    _VECTOR_AVAILABLE = False

# Cross-DB JSON Compatibility (SRE Fallback)
from sqlalchemy import JSON as SA_JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB

def SmartJSON():
    """Postgres'te JSONB, diğerlerinde (SQLite) JSON döner."""
    return PG_JSONB().with_variant(SA_JSON(), "sqlite")


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ── Kullanıcılar ─────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email          = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password= Column(String(255), nullable=False)   # bcrypt hash
    is_active      = Column(Boolean, default=True)
    is_admin       = Column(Boolean, default=False)
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    projects = relationship("Project", back_populates="owner", lazy="select")
    tokens   = relationship("RefreshToken", back_populates="user", lazy="select")


# ── JWT Refresh Token'ları ────────────────────────────────
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token      = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked    = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="tokens")


class ProjectStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    RETRYING = "RETRYING"         # Added for schema sync
    COMPLETED = "COMPLETED"
    PARTIAL_COMPLETE = "PARTIAL_COMPLETE"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"

class ProjectSource(str, enum.Enum):
    API = "api"
    MANUAL = "manual"
    TELEGRAM = "telegram"
    SCHEDULED = "scheduled"
    QUEUE_STUCK = "queue_stuck"
    APPROVAL_TIMEOUT = "approval_timeout"

class TaskPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# ── Projeler ─────────────────────────────────────────────
class Project(Base):
    __tablename__ = "projects"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id     = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
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
    # ──────────────────────────────────────────────────────
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at   = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    started_at   = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    owner    = relationship("User", back_populates="projects")
    subtasks = relationship("SubTask", back_populates="project",
                            lazy="select", cascade="all, delete-orphan")
    cost_logs= relationship("LLMCostLog", back_populates="project",
                            lazy="select", cascade="all, delete-orphan")
    task_logs= relationship("TaskLog", back_populates="project",
                            lazy="select", cascade="all, delete-orphan")


# ── Alt Görevler ─────────────────────────────────────────
class SubTask(Base):
    __tablename__ = "subtasks"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id    = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    agent_id      = Column(String(64), nullable=False, index=True)
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
    reviewed      = Column(Boolean, default=False, nullable=False)
    review_notes  = Column(SmartJSON(), default=list)
    created_at    = Column(DateTime(timezone=True), default=utcnow)
    updated_at    = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    completed_at  = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="subtasks")


# ── LLM Maliyet Logu ─────────────────────────────────────
class LLMCostLog(Base):
    __tablename__ = "llm_cost_logs"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id    = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    provider      = Column(String(64), nullable=False, index=True)
    model         = Column(String(128), nullable=False)
    agent_id      = Column(String(64), nullable=False)
    input_tokens  = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd      = Column(Float, default=0.0, nullable=False)
    latency_s     = Column(Float, default=0.0)
    success       = Column(Boolean, default=True)
    error_type    = Column(String(64), default="")
    created_at    = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project = relationship("Project", back_populates="cost_logs")


# ── Domain Event Logu (audit trail) ──────────────────────
class DomainEventLog(Base):
    __tablename__ = "domain_event_logs"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id   = Column(String(64), nullable=False, index=True)
    score      = Column(Float, nullable=False)
    state      = Column(String(32), default="healthy")
    severity   = Column(String(32), default="info")
    message    = Column(Text, default="")
    action     = Column(String(64), default="")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


# ── Webhook Abonelikleri ──────────────────────────────────
class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id   = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    url        = Column(String(2048), nullable=False)
    events     = Column(SmartJSON(), default=list)
    secret     = Column(String(64), nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    owner = relationship("User")


# ── Rate Limit Sayacı (Redis yoksa DB fallback) ───────────
class RateLimitCounter(Base):
    __tablename__ = "rate_limit_counters"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key        = Column(String(256), unique=True, nullable=False, index=True)
    count      = Column(Integer, default=0)
    window_end = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ── Görev Log Geçmişi (Faz 4) ────────────────────────────
class TaskLog(Base):
    """Her görev durum değişikliği, hata ve önemli olay buraya yazılır."""
    __tablename__ = "task_logs"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
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

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint     = Column(String(256), nullable=False, index=True)
    method       = Column(String(8), nullable=False)
    status_code  = Column(Integer, nullable=False, index=True)
    response_ms  = Column(Float, nullable=False)           # milisaniye
    user_id      = Column(UUID(as_uuid=True), nullable=True)
    ip_address   = Column(String(64), default="")
    trace_id     = Column(String(32), default="", index=True)
    error_type   = Column(String(128), default="")
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_api_metrics_endpoint_created", "endpoint", "created_at"),
        Index("ix_api_metrics_created", "created_at"),
    )


# ── Model Router Logları (Faz 12) ───────────────────────────
class ModelRouterLog(Base):
    """
    Model router tarafından verilen her kararın kaydı.
    Dashboard istatistikleri için kullanılır.
    """
    __tablename__ = "model_router_logs"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id  = Column(String(32), unique=True, nullable=False, index=True)
    username     = Column(String(128), default="")
    full_name    = Column(String(256), default="")
    is_authorized= Column(Boolean, default=False, nullable=False)
    is_admin     = Column(Boolean, default=False)
    # İlişkili sistem kullanıcısı (opsiyonel)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    command_count= Column(Integer, default=0)
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User")


# ── Telegram Komut Logu (Faz 4) ──────────────────────────
class TelegramCommandLog(Base):
    """Telegram'dan gelen tüm komutlar loglanır."""
    __tablename__ = "telegram_command_logs"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id  = Column(String(32), nullable=False, index=True)
    command      = Column(String(64), nullable=False)
    arguments    = Column(Text, default="")
    response     = Column(Text, default="")
    success      = Column(Boolean, default=True)
    project_id   = Column(UUID(as_uuid=True), nullable=True)  # komuttan oluşan görev
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


# ── Bellek / RAG Deposu (memory/store.py için) ───────────
class Memory(Base):
    """Ajan belleği — RAG sistemi için vektör + metin depolama.
    Geliştirilmiş Faz 12 Standardı: DB ile tam uyumluluk (10 kolon).
    """
    __tablename__ = "memories"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id    = Column(String(64), nullable=False, index=True)
    body        = Column("content", Text, nullable=False)            # DB'de 'content' olarak geçer
    category    = Column(String(64), default="general", nullable=False, index=True)
    importance  = Column(Float, default=0.5, nullable=False)
    metadata_   = Column(SmartJSON(), default=dict)                        # DB'de JSONB
    tags        = Column(SmartJSON(), default=list)                        # DB'de JSONB
    expires_at  = Column(DateTime(timezone=True), nullable=True)
    project_id  = Column(String(64), nullable=True, index=True)      # DB'de 'character varying'
    created_at  = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


# ── CEO Engine Modelleri (Faz 8) ──────────────────────────
class ImprovementOpportunity(Base):
    __tablename__ = "improvement_opportunities"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    status           = Column(String(32), default="open", index=True) # open, suggested, resolved
    created_at       = Column(DateTime(timezone=True), default=utcnow)

    @staticmethod
    def generate_hash(stype: str, sref: str) -> str:
        import hashlib
        return hashlib.sha256(f"{stype}:{sref}".encode()).hexdigest()


class CEOSuggestedTask(Base):
    __tablename__ = "ceo_suggested_tasks"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id   = Column(UUID(as_uuid=True), ForeignKey("improvement_opportunities.id"))
    title            = Column(String(512), nullable=False)
    description      = Column(Text)
    priority         = Column(String(16), default="medium")
    owner_agent_hint = Column(String(64))
    status           = Column(String(32), default="suggested") # suggested, approved, rejected
    reasoning_summary = Column(Text)
    impact_projection = Column(SmartJSON(), default=dict)
    created_task_id  = Column(UUID(as_uuid=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow)


class CEODecision(Base):
    __tablename__ = "ceo_decisions"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id   = Column(UUID(as_uuid=True), ForeignKey("improvement_opportunities.id"))
    decision_type    = Column(String(64)) # suggest_task, auto_approve, ignore
    decision_summary = Column(Text)
    decision_source  = Column(String(64), default="llm")
    created_at       = Column(DateTime(timezone=True), default=utcnow)



class CEOPerformanceLog(Base):
    __tablename__ = "ceo_performance_logs"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suggestion_id    = Column(UUID(as_uuid=True), ForeignKey("ceo_suggested_tasks.id"))
    project_id       = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
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

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id   = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_id     = Column(String(64), nullable=True, index=True)
    skill_id     = Column(String(64), nullable=False, index=True)
    success      = Column(Boolean, default=True, nullable=False)
    summary      = Column(Text, default="")
    data         = Column(SmartJSON(), default=dict) # Skill-specific output
    duration_s   = Column(Float, default=0.0)
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    project = relationship("Project")
