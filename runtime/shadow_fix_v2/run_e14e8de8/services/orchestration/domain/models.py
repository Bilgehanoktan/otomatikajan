from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# --- Katman 1: Interface / Input Layer ---

class SourceType(Enum):
    USER_MESSAGE = "user_message"
    TASK_REQUEST = "task_request"
    CODE_REPO = "code_repo"
    LOG_STREAM = "log_stream"
    TEST_RESULT = "test_result"
    API_CALL = "api_call"
    EVENT_STREAM = "event_stream"
    MONITORING = "monitoring"
    EPISODE_REF = "episode_ref"
    SYSTEM_EVOLUTION = "system_evolution"

@dataclass
class UnifiedInput:
    """Normalize edilmiş dış dünya girdisi."""
    input_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: SourceType = SourceType.USER_MESSAGE
    raw_payload: Any = None
    normalized_intent: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trust_level: float = 1.0  # 0.0 - 1.0
    urgency: int = 5  # 1-10
    domain_hint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- Katman 2: Perception and Interpretation Layer ---

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskType(Enum):
    ANALYSIS = "analysis"
    FIX = "fix"
    RESEARCH = "research"
    SUGGESTION = "suggestion"
    OPERATION = "operation"
    INFORMATION = "information"

@dataclass
class ProblemFrame:
    """Sistemin problemi nasıl anladığı."""
    task_type: TaskType
    objective: str
    constraints: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    evidence_required: List[str] = field(default_factory=list)
    context_scope: str = "local" # local, global, deep
    urgency: int = 5
    expected_output_type: str = "report"
    priority: int = 5
    ambiguity_score: float = 0.0
    consensus_required: bool = False
    consensus_score: float = 0.0
    
    # --- Hiyerarşik Yapı (Phase 17) ---
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    sub_tasks: List['ProblemFrame'] = field(default_factory=list)
    status: str = "pending" # pending, in_progress, completed, failed
    dependencies: List[str] = field(default_factory=list) # IDs of tasks that must finish first

# --- Katman 3: Cognitive Planning Layer ---

@dataclass
class ContextPackage:
    """Planlama için toplanan bağlam paketi."""
    working_context: str = ""
    relevant_episodes: List[str] = field(default_factory=list)
    relevant_skills: List[str] = field(default_factory=list)
    semantic_facts: List[str] = field(default_factory=list)
    graph_links: List[Dict[str, Any]] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)
    policy_hints: List[str] = field(default_factory=list)
    synapse_lessons: List[Dict[str, Any]] = field(default_factory=list)
    affective_context: Optional['AffectiveState'] = None # Phase 28
    integrity_status: Dict[str, Any] = field(default_factory=dict) # Faz 12.2: State Awareness
    thought_thread: str = ""
    north_star_vision: str = ""
    
    # --- ECC / Codex Harness Integration (Faz 12.1) ---
    selected_skill_ids: List[str] = field(default_factory=list)
    selected_rule_ids: List[str] = field(default_factory=list)
    harness_profile: str = "standard"
    skill_telemetry: Dict[str, Any] = field(default_factory=dict) # Learning Loop: performance, latency, error_rate
    harness_metadata: Dict[str, Any] = field(default_factory=dict) # Project-level ECC context

@dataclass
class PlanStep:
    step_id: str
    agent_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    verification_point: Optional[str] = None
    # Swarm Evolution (Phase 25)
    workspace_context: Dict[str, Any] = field(default_factory=dict)
    # Faz 39: Konsensüs Verileri
    consensus_required: bool = False
    consensus_score: float = 0.0
    consensus_notes: Optional[str] = None

@dataclass
class PlanProposal:
    """Tartışma (Debate) sürecindeki ham plan önerisi."""
    agent_id: str = "architect"
    content: str = ""
    title: Optional[str] = None
    steps: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    confidence: float = 1.0
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionPlan:
    """Operasyonel çekirdek için adım adım plan."""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    tool_requirements: List[str] = field(default_factory=list)
    required_context_refs: List[str] = field(default_factory=list)
    fallback_paths: Dict[str, str] = field(default_factory=dict)
    rollback_conditions: List[str] = field(default_factory=list)
    confidence_estimate: float = 1.0
    estimated_risk: RiskLevel = RiskLevel.LOW
    # Faz 12.2: Predictive Alignment
    evaluated_alternatives: List[Dict[str, Any]] = field(default_factory=list)
    # Swarm Evolution (Phase 25)
    workspace: Dict[str, Any] = field(default_factory=dict)

# --- Katman 5: Operational Execution Layer ---

@dataclass
class ActionRecord:
    """Yapılan her bir eylemin kaydı."""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    step_id: str = ""
    tool_used: str = ""
    agent_id: str = ""
    input_data: Any = None
    output_data: Any = None
    duration_s: float = 0.0
    success: bool = True
    errors: List[str] = field(default_factory=list)
    trace_ref: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Swarm Evolution (Phase 25)
    workspace_update: Optional[Dict[str, Any]] = None
    # Metacognition (Phase 27)
    cognitive_trace: Optional[Dict[str, Any]] = field(default_factory=dict) # internal reasoning pattern

# --- Katman 6: Verification and Critique Layer ---

@dataclass
class VerificationReport:
    """Çıktının doğrulama sonuçları."""
    result_status: bool
    evidence_summary: str
    unresolved_risks: List[str] = field(default_factory=list)
    confidence_adjusted: float = 1.0
    integration_reality_score: float = 0.0 # 0.0 - 1.0
    safe_to_finalize: bool = False
    safe_to_learn: bool = False
    followup_needed: List[str] = field(default_factory=list)

# --- Katman 28: Affective Core & Resilience ---

@dataclass
class AffectiveState:
    """Sistemin içsel 'duygusal' ve motivasyonel durumu."""
    motivation_level: float = 1.0 # 0.0 - 1.0 (Başarı/Başarısızlık oranı ile beslenir)
    resilience_score: float = 1.0 # Dayanıklılık (Kritik görevlerde artar)
    energy_reserve: float = 1.0   # Token bütçesi ve metabolik sağlık
    persistence_policy: str = "balanced" # careful, balanced, aggressive
    internal_stress: float = 0.0 # 0.0 - 1.0

# --- Katman 7: Memory and Learning Layer ---

@dataclass
class CausalLink:
    """İki olay arasındaki nedensellik bağı."""
    cause_id: str
    effect_id: str
    relationship_type: str # triggers, prevents, enables, causes_failure
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CausalGraph:
    """Bir bölüm içindeki veya bölümler arası nedensel ağ."""
    links: List[CausalLink] = field(default_factory=list)
    nodes_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EpisodeRecord:
    """Görevin tam yaşam döngüsü kaydı."""
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_obj: Optional[UnifiedInput] = None
    problem_frame: Optional[ProblemFrame] = None
    context_used: Optional[ContextPackage] = None
    plan: Optional[ExecutionPlan] = None
    actions: List[ActionRecord] = field(default_factory=list)
    verification: Optional[VerificationReport] = None
    final_output: Any = None
    causal_graph: Optional[CausalGraph] = None # Phase 12.5
    lessons_learned: List[str] = field(default_factory=list)
    skill_candidates: List[str] = field(default_factory=list)
    policy_candidates: List[str] = field(default_factory=list)
    world_model_updates: List[Dict[str, Any]] = field(default_factory=list)
    # Metacognition (Phase 27)
    metacognitive_score: float = 1.0 # self-assessed reasoning quality
    internal_drift_detected: bool = False
    affective_state: Optional[AffectiveState] = None # Phase 28
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class SkillArtifact:
    """Tekrar kullanılabilir skill tanımı."""
    skill_id: str
    name: str
    description: str
    trigger_pattern: str
    preconditions: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    evidence_requirements: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    confidence_score: float = 0.8
    usage_history: List[str] = field(default_factory=list)
    is_retired: bool = False

@dataclass
class PolicyProposal:
    """Davranış değişikliği önerisi."""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_policy_id: str = ""
    proposed_change: str = ""
    reason: str = ""
    supporting_evidence_episodes: List[str] = field(default_factory=list)
    expected_benefit: str = ""
    rollout_scope: str = "limited" # limited, global
    rollback_trigger: str = ""
    status: str = "pending" # pending, testing, active, rejected

# --- Katman 8: Governance and Autonomy Layer ---

class GovernanceStatus(str, Enum):
    PENDING          = "PENDING"
    QUEUED           = "QUEUED"
    RUNNING          = "RUNNING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    COMPLETED        = "COMPLETED"
    PARTIAL_COMPLETE = "PARTIAL_COMPLETE"
    ERROR            = "ERROR"
    CANCELLED        = "CANCELLED"
    PAUSED           = "PAUSED"
    RETRYING         = "RETRYING"
    SKIPPED          = "SKIPPED"

@dataclass
class GovernedTask:
    id:           str
    agent_id:     str
    prompt:       str
    status:       GovernanceStatus = GovernanceStatus.PENDING
    result:       str        = ""
    structured:   Any        = None   # AgentOutput nesnesi
    quality_score:Optional[float] = None
    quality_detail: Optional[dict] = None
    attempts:     int        = 0
    reviewed:     bool       = False
    review_notes: list       = field(default_factory=list)
    db_subtask_id: Optional[str] = None
    created_at:   datetime   = field(default_factory=lambda: datetime.now(timezone.utc))
    # Faz 39: Risk ve Konsensüs
    risk_level:   str        = "low" # low, medium, high, critical
    consensus_required: bool = False
    consensus_score: float   = 0.0
    consensus_report: Optional[str] = None
    # Faz 42: Bilişsel Devamlılık
    internal_monologue: str = ""
    # Faz 12.3: Bilişsel Çapalar (Anchors)
    causal_anchor: str = ""      # Bu alt görevin ana özeti/dersi
    inhibition_signals: list[str] = field(default_factory=list) # Kısıtlar
    # Faz 51: Rekürsif Dekompozisyon (Sovereign Depth)
    is_complex:   bool       = False
    parent_id:    Optional[str] = None
    complexity_reasoning: str = ""
    dependencies: list[str] = field(default_factory=list)

@dataclass
class SovereignGoal:
    id:         str
    title:      str
    description:str           = ""
    subtasks:   list[GovernedTask] = field(default_factory=list)
    status:     GovernanceStatus    = GovernanceStatus.PENDING
    created_at: datetime      = field(default_factory=lambda: datetime.now(timezone.utc))
    report:     str           = ""
    avg_quality:Optional[float]  = None
    workflow_template: str    = "default"
    quality_profile: str      = "standard"
    acceptance_criteria: list[str] = field(default_factory=list)
    execution_context: dict   = field(default_factory=dict)
    
    def get_shared_state(self) -> dict:
        """Paylaşılan çalışma belleğini (Blackboard) döner."""
        return self.execution_context.get("shared_state", {})

    def update_shared_state(self, updates: dict):
        """Paylaşılan belleği günceller."""
        state = self.get_shared_state()
        state.update(updates)
        self.execution_context["shared_state"] = state


# --- Katman 9: Execution Task Models ---

class TaskStatus(str, Enum):
    """Görev yürütme durumu."""
    QUEUED          = "QUEUED"
    PENDING         = "PENDING"
    RUNNING         = "RUNNING"
    COMPLETED       = "COMPLETED"
    ERROR           = "ERROR"
    CANCELLED       = "CANCELLED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    RESUMING        = "RESUMING"


@dataclass
class SubTask:
    """Bir ProjectTask içindeki alt görev birimi (Domain Model — ORM değil)."""
    id:           str = field(default_factory=lambda: str(uuid.uuid4()))
    title:        str = ""
    agent_id:     str = ""
    prompt:       str = ""
    content:      str = ""
    action:       str = ""
    description:  str = ""
    status:       TaskStatus = TaskStatus.QUEUED
    result:       str = ""
    risk_level:   str = "low"
    duration_s:   Optional[float] = None
    parent_id:    Optional[str] = None
    internal_monologue: str = ""
    is_complex:   bool = False
    attempts:     int = 0
    quality_score:Optional[float] = None
    quality_detail: Optional[dict] = field(default_factory=dict)
    reviewed:     bool       = False
    review_notes: list       = field(default_factory=list)
    dependencies: list = field(default_factory=list)


@dataclass
class ProjectTask:
    """Bir üst seviye görev/proje yürütme birimi."""
    id:           str = field(default_factory=lambda: str(uuid.uuid4()))
    title:        str = ""
    description:  str = ""
    subtasks:     List[SubTask] = field(default_factory=list)
    status:       TaskStatus = TaskStatus.QUEUED
    report:       str = ""
    risk_level:   str = "low"
    workflow_template: str = "default"
    quality_profile: str = "standard"
    acceptance_criteria: list = field(default_factory=list)
    execution_context: Dict[str, Any] = field(default_factory=dict)
    created_at:   datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_frame(self) -> Dict[str, Any]:
        """Basit sözlük temsili."""
        return {"id": self.id, "title": self.title, "description": self.description, "status": self.status.value}

