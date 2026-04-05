"""
Compatibility shim: foresight_oracle → foresight_cortex
[FIX] neural_core_orchestrator.py bu modülü doğrudan import ediyor.
ForesightCortex'in alias'ı olarak yeniden dışa açar.
"""
from packages.orchestration.agi.cognitive.foresight_cortex import (
    foresight_cortex as foresight_oracle,
    ForesightCortex as ForesightOracle,
    foresight_cortex,
)

__all__ = ["foresight_oracle", "ForesightOracle", "foresight_cortex"]
