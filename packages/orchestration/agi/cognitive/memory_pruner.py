"""
Compatibility shim: memory_pruner → dream_engine
[CONSOLIDATION] Bu modül dream_engine.py ile birleştirilmiştir.
"""
from packages.orchestration.agi.cognitive.dream_engine import (
    DreamEngine,
    dream_engine,
)

# Legacy Aliases
MemoryPruner = DreamEngine
memory_pruner = dream_engine

__all__ = ["MemoryPruner", "memory_pruner"]
