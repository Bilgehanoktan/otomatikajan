from services.repair.repair_orchestrator import (
    build_repair_case_step,
    create_repair_plan_step,
    localize_code_step,
)


def test_workflow_context_can_build_case_without_nested_input_payload(tmp_path):
    context = {
        "incident_id": "INC-FLAT-CONTEXT",
        "run_id": "RUN-FLAT-CONTEXT",
        "finding_id": "AUD-FIND-SEC-001",
        "summary": "External agent sandbox policy is incomplete.",
        "affected_files": ["configs/external_project_agent_matrix.yaml"],
        "suspected_files": ["configs/external_project_agent_matrix.yaml"],
        "allowed_paths": ["configs/"],
        "forbidden_paths": [".env", "services/auth/"],
        "output_root": str(tmp_path),
    }

    result = build_repair_case_step(context)

    assert "_context_update" in result
    assert result["repair_case"]["incident_id"] == "INC-FLAT-CONTEXT"
    assert result["repair_case"]["suspected_files"] == ["configs/external_project_agent_matrix.yaml"]


def test_workflow_steps_accept_json_safe_context_between_steps(tmp_path):
    context = {
        "incident_id": "INC-JSON-CONTEXT",
        "run_id": "RUN-JSON-CONTEXT",
        "input_payload": {
            "incident_id": "INC-JSON-CONTEXT",
            "summary": "Workflow context should survive DB persistence.",
            "suspected_files": ["configs/external_project_agent_matrix.yaml"],
            "allowed_paths": ["configs/"],
            "forbidden_paths": [".env", "services/auth/"],
        },
        "output_root": str(tmp_path),
    }

    context.update(build_repair_case_step(context)["_context_update"])
    context.update(localize_code_step(context)["_context_update"])
    result = create_repair_plan_step(context)

    assert result["repair_plan"]["incident_id"] == "INC-JSON-CONTEXT"
    assert result["_context_update"]["repair_plan"]["target_files"]
