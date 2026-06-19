from enum import Enum

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

class AgentStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"

class ArtifactType(str, Enum):
    CODE = "code"
    JSON = "json"
    MARKDOWN = "markdown"
    DIAGRAM = "diagram"
