"""
[CONSOLIDATION SHIM] improvement_v1/verifier.py -> core/improvement/cognitive_verifier.py
Legacy import redirection.
"""
from packages.orchestration.experimental.cognitive_verifier import (
    CognitiveVerifier,
    VerificationReport,
)

# Aliases
ImprovementVerifier = CognitiveVerifier
verifier = CognitiveVerifier()

__all__ = ["ImprovementVerifier", "verifier", "VerificationReport"]
