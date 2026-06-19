from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from services.project_factory.models import ProjectFactoryIntake, RequirementGate
from services.project_factory.artifacts import (
    load_project_factory_artifacts,
    write_project_factory_artifacts,
    _resolve_project_dir
)
from services.project_factory.template_registry import get_template_config
from services.project_factory.template_scaffolder import scaffold_template_files
from services.project_factory.task_planner import (
    generate_task_breakdown,
    update_task_status,
    load_task_breakdown
)
from services.project_factory.verification_runner import run_sandbox_verification
from services.project_factory.candidate_packager import package_candidate, load_candidate_manifest
from services.project_factory.implementation_logs import record_implementation_event

def _resolve_template_name(runner_mode: str) -> str:
    mapping = {
        "template_first": "fastapi-service",
        "documentation_only": "documentation-pack",
        "frontend_sandbox": "nextjs-basic-app",
        "backend_sandbox": "fastapi-service",
        "data_project": "google-sheets-tracker",
        "agent_assisted": "documentation-pack"
    }
    return mapping.get(runner_mode, "documentation-pack")

def get_implementation_run(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Loads implementation_run.json if it exists.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    run_path = project_dir / "implementation_run.json"
    if not run_path.exists():
        return None
    with open(run_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_implementation_run(
    project_id: str,
    run_data: Dict[str, Any],
    workspace_root: Optional[str] = None
) -> None:
    """
    Writes implementation_run.json.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    run_path = project_dir / "implementation_run.json"
    with open(run_path, "w", encoding="utf-8") as f:
        json.dump(run_data, f, indent=2, ensure_ascii=False)

def start_sandbox_implementation(
    project_id: str,
    operator_id: str,
    rationale: str,
    runner_mode: str = "template_first",
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synchronously runs the sandbox implementation pipeline.
    """
    # 1. Load artifacts and check status
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)

    if gate.status != "SCOPE_APPROVED":
        raise ValueError(f"Project factory {project_id} must be in SCOPE_APPROVED state to start implementation. Current: {gate.status}")

    # 2. Check duplicate run
    existing_run = get_implementation_run(project_id, workspace_root)
    if existing_run and existing_run.get("status") == "IMPLEMENTATION_RUNNING":
        raise ValueError(f"An implementation run is already in progress for project {project_id}")

    start_time = datetime.now(timezone.utc).isoformat() + "Z"
    sandbox_path = f"project_outputs/project_factory/{project_id}/sandbox"

    # 3. Create initial implementation_run
    run_data = {
        "project_id": project_id,
        "status": "IMPLEMENTATION_RUNNING",
        "runner_mode": runner_mode,
        "sandbox_path": sandbox_path,
        "started_by": operator_id,
        "started_at": start_time,
        "completed_at": None,
        "changed_files": [],
        "generated_files": [],
        "test_status": "PENDING"
    }
    write_implementation_run(project_id, run_data, workspace_root)

    # Update project states
    brief.status = "IMPLEMENTATION_RUNNING"
    gate.status = "IMPLEMENTATION_RUNNING"
    write_project_factory_artifacts(brief, gate, workspace_root)

    # Log initial start event
    record_implementation_event(
        project_id=project_id,
        event_type="IMPLEMENTATION_STARTED",
        message=f"Sandbox implementation run started by operator {operator_id} in mode '{runner_mode}'.",
        details={"operator_id": operator_id, "runner_mode": runner_mode, "rationale": rationale},
        workspace_root=workspace_root
    )

    template_name = _resolve_template_name(runner_mode)
    template_config = get_template_config(template_name, workspace_root)
    allowed_outputs = template_config.get("allowed_outputs", []) if template_config else []

    try:
        # STEP 4: PLANNING
        generate_task_breakdown(brief, template_name, allowed_outputs, workspace_root)
        update_task_status(project_id, "TASK-PLAN", "COMPLETED", workspace_root)
        record_implementation_event(
            project_id=project_id,
            event_type="PLANNING_COMPLETED",
            message="Task breakdown planned and generated.",
            details={"template": template_name},
            workspace_root=workspace_root
        )

        # STEP 5: SCAFFOLDING
        scaffolded = scaffold_template_files(project_id, template_name, workspace_root)
        update_task_status(project_id, "TASK-SCAFFOLD", "COMPLETED", workspace_root)
        record_implementation_event(
            project_id=project_id,
            event_type="SCAFFOLDING_COMPLETED",
            message=f"Boilerplate files scaffolded: {', '.join(scaffolded)}",
            details={"scaffolded_files": scaffolded},
            workspace_root=workspace_root
        )

        # Update TASK-GEN items to COMPLETED
        breakdown = load_task_breakdown(project_id, workspace_root)
        for task in breakdown:
            if task.task_id.startswith("TASK-GEN"):
                update_task_status(project_id, task.task_id, "COMPLETED", workspace_root)

        # STEP 6: VERIFICATION
        verification = run_sandbox_verification(project_id, template_name, workspace_root)
        test_status = verification.get("status", "FAILED")
        update_task_status(project_id, "TASK-VERIFY", "COMPLETED", workspace_root)
        record_implementation_event(
            project_id=project_id,
            event_type="VERIFICATION_COMPLETED",
            message=f"Verification finished with status: {test_status}",
            details=verification,
            workspace_root=workspace_root
        )

        if test_status == "PASSED":
            # STEP 7: PACKAGING
            test_cmds = template_config.get("test_commands", []) if template_config else []
            package_manifest = package_candidate(
                project_id=project_id,
                template_name=template_name,
                verification_status=test_status,
                test_commands=test_cmds,
                workspace_root=workspace_root
            )
            update_task_status(project_id, "TASK-PACKAGE", "COMPLETED", workspace_root)
            record_implementation_event(
                project_id=project_id,
                event_type="CANDIDATE_PACKAGED",
                message="Implementation candidate successfully packaged for operator Human Gate review.",
                details=package_manifest,
                workspace_root=workspace_root
            )

            # Mark state as succeeded
            completed_time = datetime.now(timezone.utc).isoformat() + "Z"
            run_data.update({
                "status": "IMPLEMENTATION_SUCCEEDED",
                "completed_at": completed_time,
                "generated_files": scaffolded,
                "test_status": "PASSED"
            })
            write_implementation_run(project_id, run_data, workspace_root)

            brief.status = "HUMAN_GATE_WAITING"
            gate.status = "HUMAN_GATE_WAITING"
            write_project_factory_artifacts(brief, gate, workspace_root)

        else:
            # Verification failed
            completed_time = datetime.now(timezone.utc).isoformat() + "Z"
            run_data.update({
                "status": "IMPLEMENTATION_FAILED",
                "completed_at": completed_time,
                "generated_files": scaffolded,
                "test_status": "FAILED"
            })
            write_implementation_run(project_id, run_data, workspace_root)

            brief.status = "IMPLEMENTATION_FAILED"
            gate.status = "IMPLEMENTATION_FAILED"
            write_project_factory_artifacts(brief, gate, workspace_root)

            record_implementation_event(
                project_id=project_id,
                event_type="IMPLEMENTATION_FAILED",
                message="Verification failed. Implementation runner terminated.",
                details=verification,
                workspace_root=workspace_root
            )

    except Exception as e:
        # Error during execution
        completed_time = datetime.now(timezone.utc).isoformat() + "Z"
        run_data.update({
            "status": "IMPLEMENTATION_FAILED",
            "completed_at": completed_time,
            "test_status": "FAILED"
        })
        write_implementation_run(project_id, run_data, workspace_root)

        brief.status = "IMPLEMENTATION_FAILED"
        gate.status = "IMPLEMENTATION_FAILED"
        write_project_factory_artifacts(brief, gate, workspace_root)

        record_implementation_event(
            project_id=project_id,
            event_type="IMPLEMENTATION_FAILED",
            message=f"Runner exception occurred: {e}",
            details={"error": str(e)},
            workspace_root=workspace_root
        )

    return get_implementation_run(project_id, workspace_root)

def cancel_sandbox_implementation(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancels any active implementation runner for the project.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    run_data = get_implementation_run(project_id, workspace_root)

    # We allow canceling if status is IMPLEMENTATION_RUNNING or IMPLEMENTATION_READY
    if not run_data or run_data.get("status") not in ["IMPLEMENTATION_RUNNING", "IMPLEMENTATION_READY"]:
        raise ValueError(f"No active running implementation found for project {project_id} that can be cancelled.")

    completed_time = datetime.now(timezone.utc).isoformat() + "Z"
    run_data.update({
        "status": "CANCELLED",
        "completed_at": completed_time
    })
    write_implementation_run(project_id, run_data, workspace_root)

    brief.status = "CANCELLED"
    gate.status = "CANCELLED"
    write_project_factory_artifacts(brief, gate, workspace_root)

    record_implementation_event(
        project_id=project_id,
        event_type="IMPLEMENTATION_CANCELLED",
        message="Sandbox implementation runner cancelled by operator request.",
        workspace_root=workspace_root
    )

    return run_data
