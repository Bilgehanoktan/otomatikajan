"""
Compatibility shim: consolidator → dream_engine
[CONSOLIDATION] Bu modül dream_engine.py ile birleştirilmiştir.
"""
from packages.orchestration.agi.cognitive.dream_engine import (
    DreamEngine,
    dream_engine,
    start_dream_loop,
)
from db.session import session_scope

# Legacy Aliases
Consolidator = DreamEngine
consolidator = dream_engine

# Robust shim for run_cycle (used in lifespan.py)
if not hasattr(consolidator, "run_cycle"):
    async def _run_cycle_shim():
        async with session_scope() as db:
            await consolidator.run_dream_cycle(db)
    consolidator.run_cycle = _run_cycle_shim

start_consolidation_loop = start_dream_loop

__all__ = ["Consolidator", "consolidator", "start_consolidation_loop"]

