"""
Compatibility shim: reflection_cortex → metacognitive_auditor
[REFLECTION] Bu modül metacognitive_auditor.py ile birleştirilmiştir.
"""
from core.agi.cognitive.metacognitive_auditor import (
    MetacognitiveAuditor,
    metacognitive_auditor,
    start_reflection_loop,
)

# Legacy Aliases
ReflectionCortex = MetacognitiveAuditor
reflection_cortex = metacognitive_auditor

__all__ = ["ReflectionCortex", "reflection_cortex", "start_reflection_loop"]
