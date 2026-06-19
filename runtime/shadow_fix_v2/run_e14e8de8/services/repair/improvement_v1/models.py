"""
[CONSOLIDATION SHIM] improvement_v1/libs.db.models.py -> core/improvement/libs.db.models.py
Legacy import redirection.
"""
from hub_cortex.improvement_engine.models import *

# Legacy common names
TaskState = TaskState
ImprovementTask = ImprovementTask

__all__ = ["TaskState", "ImprovementTask"]

