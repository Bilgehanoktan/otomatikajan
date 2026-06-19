"""
Compatibility shim: evolutionary_executor → evolution_engine
[CONSOLIDATION] Bu modül evolution_engine.py ile birleştirilmiştir.
"""
from services.orchestration.agi.cognitive.evolution_engine import (
    SovereignEvolutionEngine,
    evolution_engine,
)

# Legacy Aliases
EvolutionaryExecutor = SovereignEvolutionEngine
evolutionary_executor = evolution_engine

__all__ = ["EvolutionaryExecutor", "evolutionary_executor"]
