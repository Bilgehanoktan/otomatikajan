"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya dairesel bağımlılık kilitlerini (Circular Hang) kırmak için 
dinamik (on-demand) yükleme yapar.
"""

def get_sovereign_cortex():
    # Local import to shatter Phase 12.4 circular deadlocks
    from packages.orchestration.application.sovereign_cortex import get_sovereign_cortex as _get
    return _get()

# Note: Proxying top-level attributes to dynamic getters
def __getattr__(name):
    if name in ["sovereign_cortex", "nexus_orchestrator"]:
        return get_sovereign_cortex()
    if name == "SovereignCortex":
        from packages.orchestration.application.sovereign_cortex import SovereignCortex
        return SovereignCortex
    raise AttributeError(f"module {__name__} has no attribute {name}")
