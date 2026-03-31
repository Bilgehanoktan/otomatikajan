from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# ── 1. GÖREV YAŞAM DÖNGÜSÜ (TASK LIFECYCLE) ─────────────
class TaskState(str, Enum):
    # Başlangıç
    CREATED = "created"           
    VALIDATED = "validated"       
    QUEUED = "queued"             
    # Yürütme
    ASSIGNED = "assigned"         
    RUNNING = "running"           
    # Müdahale
    HEALING = "healing"           
    AWAITING_APPROVAL = "awaiting_approval" 
    RETRYING = "retrying"
    # Bitiş
    SYNTHESIZING = "synthesizing" 
    COMPLETED = "completed"       
    PARTIAL_COMPLETE = "partial_complete" 
    FAILED = "failed"             
    CANCELLED = "cancelled"       

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
