from __future__ import annotations

from typing import Dict, Any
from services.project_factory.models import ProjectFactoryIntake, RequirementGate

def build_project_factory_intake(finding: Dict[str, Any], audit_run_id: str) -> ProjectFactoryIntake:
    """
    Constructs a ProjectFactoryIntake from a CEO suggestions finding dictionary.
    """
    finding_id = finding.get("finding_id")
    if not finding_id:
        raise ValueError("finding_id is required in the finding payload to construct an intake")

    project_id = f"PF-{finding_id}"
    title = finding.get("title", f"Project Factory Intake for {finding_id}")
    problem_statement = finding.get("description", "No description provided.")
    recommended_action = finding.get("recommended_action") or ""
    if not recommended_action:
        rec_actions = finding.get("recommended_actions")
        if isinstance(rec_actions, list) and len(rec_actions) > 0:
            recommended_action = ", ".join(str(a) for a in rec_actions)
        elif isinstance(rec_actions, str):
            recommended_action = rec_actions

    affected_files = finding.get("affected_files") or []
    if isinstance(affected_files, str):
        import json
        try:
            affected_files = json.loads(affected_files)
        except Exception:
            affected_files = [affected_files]

    return ProjectFactoryIntake(
        project_id=project_id,
        source_suggestion_id=finding_id,
        audit_run_id=audit_run_id,
        title=title,
        problem_statement=problem_statement,
        recommended_action=recommended_action,
        affected_files=affected_files,
        suggested_scope="mvp",
        status="REQUIREMENT_GATE_WAITING",
        requires_operator_approval=True
    )

def build_initial_requirement_gate() -> RequirementGate:
    """
    Returns the initial requirement approval gate state.
    """
    return RequirementGate(
        gate="Requirement Approval Gate",
        status="WAITING_FOR_OPERATOR",
        allowed_actions=["approve_scope", "request_revision", "reject"],
        implementation_allowed=False
    )
