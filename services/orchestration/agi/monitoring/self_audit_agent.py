"""
Compatibility shim: self_audit_agent (monitoring) → metacognitive_auditor
[CONSOLIDATION] Bu modül metacognitive_auditor.py ile birleştirilmiştir.
"""
from services.orchestration.agi.cognitive.metacognitive_auditor import (
    MetacognitiveAuditor,
    metacognitive_auditor,
)

# Legacy Aliases
SelfAuditAgent = MetacognitiveAuditor
self_audit_agent = metacognitive_auditor

__all__ = ["SelfAuditAgent", "self_audit_agent"]
