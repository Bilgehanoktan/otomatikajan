"""
[CONSOLIDATION SHIM] improvement_v1/verifier.py -> core/improvement/cognitive_verifier.py
Legacy import redirection.
"""
from hub_cortex.improvement_engine.cognitive_verifier import (
    CognitiveVerifier,
    VerificationReport,
)

# Aliases
ImprovementVerifier = CognitiveVerifier
verifier = CognitiveVerifier()

__all__ = ["ImprovementVerifier", "verifier", "VerificationReport"]

