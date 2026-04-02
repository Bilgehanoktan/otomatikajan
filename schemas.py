from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# ── 1. GÖREV YAŞAM DÖNGÜSÜ (TASK LIFECYCLE) ─────────────
class TaskState(str, Enum):
    # Başlangıç
    PENDING = "PENDING"           # Beklemede (init)
    CREATED = "created"           # Oluşturuldu (core uyumluluk)
    VALIDATED = "validated"       # Doğrulandı (core uyumluluk)
    QUEUED = "QUEUED"             # Kuyrukta (Celery)
    
    # Yürütme
    ASSIGNED = "assigned"         # Atandı (core uyumluluk)
    RUNNING = "RUNNING"           # Çalışıyor
    
    # Müdahale / Ara Durumlar
    PENDING_APPROVAL = "PENDING_APPROVAL" # Onay Bekliyor
    AWAITING_APPROVAL = "awaiting_approval" # Onay Bekliyor (core uyumluluk)
    PAUSED = "PAUSED"             # Duraklatıldı
    RETRYING = "RETRYING"         # Yeniden Deneniyor
    HEALING = "healing"           # İyileştirme (core uyumluluk)
    SYNTHESIZING = "synthesizing" # Sentezleme (core uyumluluk)
    
    # Bitiş
    COMPLETED = "COMPLETED"       # Tamamlandı
    PARTIAL_COMPLETE = "PARTIAL_COMPLETE" # Kısmen Tamamlandı
    ERROR = "ERROR"               # Hata (Failed)
    FAILED = "failed"             # Hata (core uyumluluk)
    CANCELLED = "CANCELLED"       # İptal Edildi

# ── 1b. DEERFLOW OLAY TİPLERİ (STREAM EVENT TYPES) ──────
class DeerFlowEventType(str, Enum):
    THOUGHT = "thought"
    PLAN_STEP = "plan_step"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ARTIFACT_CREATED = "artifact_created"
    WARNING = "warning"
    FINAL_ANSWER = "final_answer"
    USAGE = "usage"
    ERROR = "error"

# ── 2. AJAN SÖZLEŞMELERİ (AGENT CONTRACTS) ──────────────
class AgentStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"

class ArtifactType(str, Enum):
    CODE = "code"
    JSON = "json"
    MARKDOWN = "markdown"
    DIAGRAM = "diagram"

class Artifact(BaseModel):
    name: str
    type: ArtifactType
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ErrorDetail(BaseModel):
    error_type: str 
    message: str
    traceback: Optional[str] = None
    is_recoverable: bool = True

class SubtaskOutput(BaseModel):
    """Ajanların dönmek zorunda olduğu standart format"""
    task_id: str
    subtask_id: str
    agent_id: str
    
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0
    
    status: AgentStatus
    summary: str
    raw_output: str
    artifacts: List[Artifact] = Field(default_factory=list)
    error: Optional[ErrorDetail] = None
    
    started_at: datetime
    completed_at: datetime

# ── 3. NİHAİ RAPOR SÖZLEŞMESİ (FINAL REPORT) ────────────
class AgentContribution(BaseModel):
    agent_id: str
    status: str
    summary: str
    cost_contribution: float
    
class FinalReport(BaseModel):
    """Müşteriye/Arayüze sunulacak sentezlenmiş sonuç"""
    task_id: str
    executive_summary: str
    consolidated_artifacts: List[Artifact] = Field(default_factory=list)
    contributions: List[AgentContribution]
    total_cost_usd: float
    total_latency_s: float
    unresolved_issues: List[str] = Field(default_factory=list)
    needs_human_action: bool = False
