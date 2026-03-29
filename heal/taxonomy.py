from enum import Enum
from pydantic import BaseModel
from typing import Optional

class FailureCategory(str, Enum):
    """Hataların Sınıflandırılması"""
    PROVIDER_LIMIT = "provider_limit"       # 429 Rate Limit
    PROVIDER_TIMEOUT = "provider_timeout"   # 504 Timeout
    EMPTY_OUTPUT = "empty_output"           # LLM boş yanıt döndü
    FORMAT_ERROR = "format_error"           # JSON Parse hatası
    CODE_HALLUCINATION = "hallucination"    # Üretilen kod sentaks hatalı
    INFRA_ERROR = "infra_error"             # DB veya Redis çöktü
    AUTH_ERROR = "auth_error"               # Yanlış API Key

class RepairAction(str, Enum):
    """Sistemin verebileceği tepkiler"""
    RETRY_SAME = "retry_same_model"
    RETRY_WITH_DELAY = "retry_with_exponential_backoff"
    ROTATE_MODEL = "rotate_to_fallback_model"
    SIMPLIFY_PROMPT = "simplify_prompt_and_retry"
    ESCALATE_TO_HUMAN = "escalate_to_human_approval"
    ABORT_CRITICAL = "abort_task_and_alert_admin"

class FailureRecord(BaseModel):
    """Her hatanın DB'ye kaydedilecek kanıtı"""
    task_id: str
    subtask_id: Optional[str]
    category: FailureCategory
    raw_error: str
    attempt_count: int
    applied_action: RepairAction