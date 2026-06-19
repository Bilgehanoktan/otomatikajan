"""
Compatibility shim: sovereign_auditor → hub_cortex.domain.auditor
[FAZ 12.1] Bu modül artık merkezi domain denetçisine yönlendirme yapmaktadır.
"""
from services.orchestration.domain.auditor import (
    MetacognitiveAuditor,
    metacognitive_auditor,
)

# Legacy Aliases
SovereignCortexAuditor = MetacognitiveAuditor
sovereign_auditor = metacognitive_auditor

__all__ = ["SovereignCortexAuditor", "sovereign_auditor"]
