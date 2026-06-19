"""
Compatibility shim: meta_audit → metacognitive_auditor
[CONSOLIDATION] Bu modül metacognitive_auditor.py ile birleştirilmiştir.
"""
from services.orchestration.agi.cognitive.metacognitive_auditor import (
    MetacognitiveAuditor,
    metacognitive_auditor,
)

# Legacy Aliases
MetaAudit = MetacognitiveAuditor
meta_audit = metacognitive_auditor

__all__ = ["MetaAudit", "meta_audit"]
