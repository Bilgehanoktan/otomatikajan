from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

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
    working_context: str
    relevant_episodes: List[str] = field(default_factory=list)
    relevant_skills: List[str] = field(default_factory=list)
    semantic_facts: List[str] = field(default_factory=list)
    graph_links: List[Dict[str, Any]] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)
    policy_hints: List[str] = field(default_factory=list)

@dataclass
class PlanStep:
    step_id: str
    agent_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    verification_point: Optional[str] = None

@dataclass
class PlanProposal:
    """Tartışma (Debate) sürecindeki ham plan önerisi."""
    agent_id: str
    content: str
    confidence: float = 1.0
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

# --- Katman 5: Operational Execution Layer ---

@dataclass
class ActionRecord:
    """Yapılan her bir eylemin kaydı."""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    step_id: str = ""
    tool_used: str = ""
    input_data: Any = None
    output_data: Any = None
    duration_s: float = 0.0
    success: bool = True
    errors: List[str] = field(default_factory=list)
    trace_ref: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

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
