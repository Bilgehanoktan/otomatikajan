"""
Compatibility shim: sovereign_auditor → metacognitive_auditor
[CONSOLIDATION] Bu modül metacognitive_auditor.py ile birleştirilmiştir.
"""
from packages.orchestration.agi.cognitive.metacognitive_auditor import (
    MetacognitiveAuditor,
    metacognitive_auditor,
)

# Legacy Aliases
SovereignCortexAuditor = MetacognitiveAuditor
sovereign_auditor = metacognitive_auditor

__all__ = ["SovereignCortexAuditor", "sovereign_auditor"]
