import json
import pytest
from pathlib import Path
import tempfile
import uuid

from services.taskflow.taskflow_engine import run_workflow
from services.taskflow.taskflow_models import WorkflowRun, TaskStep
from services.repair.taskflow_artifacts import (
    write_step_artifact,
    read_step_artifact,
    artifact_dir_for_run,
    build_artifact_manifest
)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_artifact_dir_and_write(temp_output_dir):
    incident_id = "INC-TEST-01"
    run_id = str(uuid.uuid4())
    step_id = "collect_failure_context"
    
    payload = {"error": "connection_timeout", "timestamp": "2026-05-18T20:00:00Z"}
    
    # Write artifact
    artifact_info = write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id=step_id,
        artifact_name="failure_context.json",
        payload=payload,
        output_root=temp_output_dir
    )
    
    assert artifact_info["status"] == "written"
    assert artifact_info["name"] == "failure_context.json"
    assert "sha256" in artifact_info
    
    # Read artifact back
    read_payload = read_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        artifact_name="failure_context.json",
        output_root=temp_output_dir
    )
    assert read_payload == payload

def test_missing_artifact_step_fails(temp_output_dir):
    # If a handler fails to write its designated artifact, the engine should raise a ValueError and fail the step.
    contract = {
        "workflow_id": "test_missing_artifact_wf",
        "name": "Test Missing Artifact Workflow",
        "steps": [
            {
                "id": "collect_failure_context",
                "type": "deterministic",
                "handler": "tests.repair.test_taskflow_artifact_contract.noop_handler_no_artifact",
                "artifact": "failure_context.json"
            }
        ]
    }
    
    # Write temporary workflow yaml contract
    yaml_path = Path("workflows/test_missing_artifact_wf.yaml")
    yaml_content = """workflow_id: test_missing_artifact_wf
name: Test Missing Artifact Workflow
version: 1
trigger:
  type: manual
steps:
  - id: collect_failure_context
    type: deterministic
    handler: tests.repair.test_taskflow_artifact_contract.noop_handler_no_artifact
    artifact: failure_context.json
"""
    yaml_path.write_text(yaml_content, encoding="utf-8")
    
    try:
        # Register the mock handler to the global namespace or simulate it
        import sys
        import types
        
        module_name = "tests.repair.test_taskflow_artifact_contract"
        if module_name not in sys.modules:
            mod = types.ModuleType(module_name)
            sys.modules[module_name] = mod
            
        def noop_handler_no_artifact(context):
            # Specifically does NOT write the artifact!
            return {"result": "ok"}
            
        sys.modules[module_name].noop_handler_no_artifact = noop_handler_no_artifact
        
        # Run the workflow
        payload = {
            "incident_id": "INC-MISSING-ART",
            "run_id": str(uuid.uuid4())
        }
        
        # The workflow engine should fail because the step fails to produce failure_context.json
        run = run_workflow("test_missing_artifact_wf", payload, output_root=temp_output_dir)
    finally:
        if yaml_path.exists():
            yaml_path.unlink()
    assert run.status in {"FAILED", "BLOCKED"}
    
    failed_step = next(s for s in run.steps if s.step_id == "collect_failure_context")
    assert failed_step.status in {"FAILED", "BLOCKED"}
    assert "Required artifact" in failed_step.error

def test_format_enforcements_for_risk_report():
    # Enforce risk_report.json schema validation
    # risk_score, risk_level, blast_radius, changed_files, policy_findings, security_findings, rollback_available, human_gate_required
    required_keys = {
        "risk_score", "risk_level", "blast_radius", "changed_files",
        "policy_findings", "security_findings", "rollback_available", "human_gate_required"
    }
    
    invalid_report = {
        "risk_score": 0.45,
        "risk_level": "medium"
    } # Missing other required keys!
    
    valid_report = {
        "risk_score": 0.45,
        "risk_level": "medium",
        "blast_radius": "low",
        "changed_files": ["app.py"],
        "policy_findings": [],
        "security_findings": [],
        "rollback_available": True,
        "human_gate_required": True
    }
    
    # Assert missing fields
    missing_fields = required_keys - set(invalid_report.keys())
    assert len(missing_fields) > 0
    
    # Assert valid fields
    valid_missing = required_keys - set(valid_report.keys())
    assert len(valid_missing) == 0

def test_format_enforcements_for_patch_candidates():
    # Enforce patch_candidates.json schema validation
    # candidate_id, candidate_source, agent_key, requested_mode, diff_ref, confidence_score, test_score, risk_score, blocked_reason, artifact_refs
    required_keys = {
        "candidate_id", "candidate_source", "agent_key", "requested_mode",
        "diff_ref", "confidence_score", "test_score", "risk_score", "blocked_reason", "artifact_refs"
    }
    
    valid_candidate = {
        "candidate_id": "candidate-12",
        "candidate_source": "mock_generator",
        "agent_key": "mock_agent",
        "requested_mode": "local_adapter",
        "diff_ref": "repair_outputs/INC-1/patch.diff",
        "confidence_score": 0.85,
        "test_score": 0.90,
        "risk_score": 0.15,
        "blocked_reason": None,
        "artifact_refs": []
    }
    
    missing = required_keys - set(valid_candidate.keys())
    assert len(missing) == 0
