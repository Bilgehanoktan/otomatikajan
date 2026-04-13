"""
[DEPRECATED] improvement_v1/models.py
Compatibility shim — all models moved to core.improvement.models
"""
from hub_cortex.improvement.models import (
    ImprovementOpportunity,
    PatchProposal,
    VerificationResult,
    GateDecision,
)

__all__ = ["ImprovementOpportunity", "PatchProposal", "VerificationResult", "GateDecision"]
