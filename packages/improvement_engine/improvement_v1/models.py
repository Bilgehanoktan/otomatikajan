"""
[CONSOLIDATION SHIM] improvement_v1/models.py -> core/improvement/models.py
Legacy import redirection.
"""
from core.improvement.models import *

# Legacy common names
TaskState = TaskState
ImprovementTask = ImprovementTask

__all__ = ["TaskState", "ImprovementTask"]
