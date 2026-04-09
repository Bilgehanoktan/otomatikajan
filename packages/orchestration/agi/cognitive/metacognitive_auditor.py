"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'packages.orchestration.domain.auditor' modülüne yönlendirme yapmaktadır.
Yeni geliştirmelerde doğrudan 'domain.auditor' kullanılmalıdır.
"""

from packages.orchestration.domain.auditor import (
    MetacognitiveAuditor,
    metacognitive_auditor,
    ReflectionCortex,
    DiagnosticNode,
    reflection_cortex,
    start_reflection_loop
)
