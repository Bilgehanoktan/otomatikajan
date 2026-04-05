"""
Self-Repair Architecture — Faz 4
Observe -> Diagnose -> Patch -> Verify -> Gate -> PR

Bu modül:
1. Incident'leri normalize eder
2. Kök neden analizi yapar
3. Minimal patch planlar ve üretir
4. Sandbox'ta doğrular
5. Policy kontrolü uygular
6. PR önerisi hazırlar

ÖNEMLİ: Otomatik merge KAPALI. İnsan onayı zorunlu.
"""

from .schemas import (
    IncidentRecord, IncidentSource, IncidentSeverity,
    DiagnosisTicket, ProblemClass, RepairMode,
    PatchPlan, RiskLevel,
    ValidationReport, ValidationStatus,
    RepairJob, RepairJobStatus,
)
from .ingestion import incident_ingestor, IncidentIngestor
from .triage import triage_engine, TriageEngine
from .memory import incident_memory, patch_memory, architecture_memory

__all__ = [
    "IncidentRecord", "IncidentSource", "IncidentSeverity",
    "DiagnosisTicket", "ProblemClass", "RepairMode",
    "PatchPlan", "RiskLevel",
    "ValidationReport", "ValidationStatus",
    "RepairJob", "RepairJobStatus",
    "incident_ingestor", "IncidentIngestor",
    "triage_engine", "TriageEngine",
    "incident_memory", "patch_memory", "architecture_memory",
]
