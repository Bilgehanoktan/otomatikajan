"""
Compatibility shim: subconscious_cortex_45 → dream_engine
[CONSOLIDATION] Bu modül dream_engine.py ile birleştirilmiştir.
"""
from packages.orchestration.agi.cognitive.dream_engine import dream_engine

# Legacy Aliases
SubconsciousCortex45 = type(dream_engine)
subconscious_cortex_45 = dream_engine
# Alias for backward compatibility
if not hasattr(subconscious_cortex_45, "dream"):
    subconscious_cortex_45.dream = dream_engine.run_dream_cycle

__all__ = ["SubconsciousCortex45", "subconscious_cortex_45"]
