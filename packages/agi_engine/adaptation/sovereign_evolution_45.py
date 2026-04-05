"""
Compatibility shim: sovereign_evolution_45 → evolution_engine
[CONSOLIDATION] Bu modül evolution_engine.py ile birleştirilmiştir.
"""
from core.agi.cognitive.evolution_engine import (
    SovereignEvolutionEngine,
    evolution_engine,
)

# Legacy Aliases
SovereignEvolution45 = SovereignEvolutionEngine
sovereign_evolution_45 = evolution_engine

__all__ = ["SovereignEvolution45", "sovereign_evolution_45"]
