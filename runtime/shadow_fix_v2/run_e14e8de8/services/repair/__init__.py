"""Self-repair package entrypoint.

Imports are intentionally lazy so running the Phase 1-3 CLI does not initialize
the legacy long-running repair stack or its optional runtime dependencies.
"""

__all__ = [
    "IncidentRecord",
    "IncidentSource",
    "IncidentSeverity",
    "DiagnosisTicket",
    "ProblemClass",
    "RepairMode",
    "PatchPlan",
    "RiskLevel",
    "ValidationReport",
    "ValidationStatus",
    "RepairJob",
    "RepairJobStatus",
    "incident_ingestor",
    "IncidentIngestor",
    "triage_engine",
    "TriageEngine",
    "incident_memory",
    "patch_memory",
    "architecture_memory",
]


def __getattr__(name: str):
    if name in {
        "IncidentRecord",
        "IncidentSource",
        "IncidentSeverity",
        "DiagnosisTicket",
        "ProblemClass",
        "RepairMode",
        "PatchPlan",
        "RiskLevel",
        "ValidationReport",
        "ValidationStatus",
        "RepairJob",
        "RepairJobStatus",
    }:
        from . import schemas

        return getattr(schemas, name)

    if name in {"incident_ingestor", "IncidentIngestor"}:
        from . import ingestion

        return getattr(ingestion, name)

    if name in {"triage_engine", "TriageEngine"}:
        from . import triage

        return getattr(triage, name)

    if name in {"incident_memory", "patch_memory", "architecture_memory"}:
        from . import memory

        return getattr(memory, name)

    raise AttributeError(name)
