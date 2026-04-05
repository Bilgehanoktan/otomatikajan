"""
Compatibility shim: compactor → dream_engine
[CONSOLIDATION] Bu modül dream_engine.py ile birleştirilmiştir.
"""
from packages.orchestration.agi.cognitive.dream_engine import (
    DreamEngine,
    dream_engine,
)

# Legacy Aliases
ContextCompactor = DreamEngine
context_compactor = dream_engine

__all__ = ["ContextCompactor", "context_compactor"]
