"""
Compatibility shim: metacognition → metacognitive_auditor
[CONSOLIDATION] Bu modül metacognitive_auditor.py ile birleştirilmiştir.
"""
from services.orchestration.agi.cognitive.metacognitive_auditor import (
    MetacognitiveAuditor,
    metacognitive_auditor,
)

# Legacy Aliases
MetacognitiveNode = MetacognitiveAuditor
metacognition = metacognitive_auditor

__all__ = ["MetacognitiveNode", "metacognition"]
