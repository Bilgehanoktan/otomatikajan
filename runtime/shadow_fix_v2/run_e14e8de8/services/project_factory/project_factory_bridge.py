from __future__ import annotations

from typing import Dict, Any, Optional
from services.project_factory.intake_builder import build_project_factory_intake, build_initial_requirement_gate
from services.project_factory.artifacts import write_project_factory_artifacts

def bridge_suggestion_to_project_factory(
    finding: Dict[str, Any],
    audit_run_id: str,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Bridges a suggestion finding to the Project Factory by:
    - Constructing the intake payload
    - Creating the Requirement Gate
    - Persisting the corresponding artifacts
    Returns bridge execution metadata.
    """
    intake = build_project_factory_intake(finding, audit_run_id)
    gate = build_initial_requirement_gate()
    
    write_project_factory_artifacts(intake, gate, workspace_root)

    return {
        "status": "created",
        "project_id": intake.project_id,
        "source_suggestion_id": intake.source_suggestion_id,
        "audit_run_id": intake.audit_run_id,
        "project_brief_ref": f"project_outputs/project_factory/{intake.project_id}/project_brief.json",
        "requirement_gate_ref": f"project_outputs/project_factory/{intake.project_id}/requirement_gate.json",
        "status_state": intake.status
    }
