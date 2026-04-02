"""
Compatibility shim: consolidator → dream_engine
[CONSOLIDATION] Bu modül dream_engine.py ile birleştirilmiştir.
"""
from core.agi.cognitive.dream_engine import (
    DreamEngine,
    dream_engine,
)

# Legacy Aliases
Consolidator = DreamEngine
consolidator = dream_engine

__all__ = ["Consolidator", "consolidator"]
