import json
import shutil
import tempfile
import hashlib
from pathlib import Path
import pytest
from fastapi import FastAPI

from services.repair.release_readiness import (
    load_matrix_config,
    build_contract_matrix,
    validate_api_contracts,
    validate_frontend_backend_parity,
    validate_artifact_contract,
    build_release_readiness_report
)

@pytest.fixture
def temp_run_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_contract_matrix_contains_ceo_and_repair_lab_routes():
    matrix = build_contract_matrix(app=None)
    assert len(matrix) > 0
    # Assert contains key endpoints
    routes = [x["route_or_artifact"] for x in matrix]
    assert "/api/v1/ceo/overview" in routes
    assert "/api/v1/repair-lab/runs/{run_id}/tournament" in routes

def test_artifact_validator_detects_missing_required_artifact(temp_run_dir):
    # Required artifact not present -> blocks release
    # Let's create an empty artifact_manifest.json to avoid untracked issues
    manifest = {}
    (temp_run_dir / "artifact_manifest.json").write_text(json.dumps(manifest))
    
    results, is_blocked = validate_artifact_contract(temp_run_dir)
    assert is_blocked
    
    # Check that required artifact repair_case.json is marked missing
    repair_case_status = next(x for x in results if x["artifact_name"] == "repair_case.json")
    assert repair_case_status["status"] == "missing"
    assert repair_case_status["blocking"] is True

def test_artifact_validator_detects_hash_mismatch(temp_run_dir):
    # Create required files
    config = load_matrix_config()
    artifact_schemas = config.get("artifact_schemas", [])
    
    manifest = {}
    for schema in artifact_schemas:
        name = schema.get("artifact_name", "")
        # Create correct file content
        file_path = temp_run_dir / name
        file_path.write_text("dummy-data", encoding="utf-8")
        manifest[name] = {"sha256": "wrong-hash"}
        
    (temp_run_dir / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    
    results, is_blocked = validate_artifact_contract(temp_run_dir)
    assert is_blocked
    
    # Assert hash mismatch is caught and blocks
    mismatch = next(x for x in results if x["status"] == "hash_mismatch")
    assert mismatch["blocking"] is True

def test_selected_candidate_mismatch_blocks_release(temp_run_dir):
    # Write matching manifest so missing artifacts don't interfere
    config = load_matrix_config()
    artifact_schemas = config.get("artifact_schemas", [])
    manifest = {}
    for schema in artifact_schemas:
        name = schema.get("artifact_name", "")
        file_path = temp_run_dir / name
        content = "{}"
        if name == "tournament_result.json":
            content = json.dumps({"selected_candidate_id": "cand-1"})
        elif name == "human_gate_decision.json":
            content = json.dumps({"selected_candidate_id": "cand-2", "status": "APPROVED"})
        elif name == "draft_pr_metadata.json":
            content = json.dumps({})
        elif name == "pr_review.json":
            content = json.dumps({"status": "completed"})
            
        file_path.write_text(content, encoding="utf-8")
        
        # Calculate SHA256 for manifest
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        manifest[name] = {"sha256": sha}
        
    (temp_run_dir / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    
    results, is_blocked = validate_artifact_contract(temp_run_dir)
    assert is_blocked
    mismatch_entry = next(x for x in results if x["status"] == "integrity_failed" and "selected_candidate" in x["artifact_name"])
    assert mismatch_entry["blocking"] is True

def test_draft_pr_without_pr_review_blocks_release(temp_run_dir):
    config = load_matrix_config()
    artifact_schemas = config.get("artifact_schemas", [])
    manifest = {}
    for schema in artifact_schemas:
        name = schema.get("artifact_name", "")
        file_path = temp_run_dir / name
        content = "{}"
        if name == "tournament_result.json":
            content = json.dumps({"selected_candidate_id": "cand-1"})
        elif name == "human_gate_decision.json":
            content = json.dumps({"selected_candidate_id": "cand-1", "status": "APPROVED"})
        elif name == "draft_pr_metadata.json":
            content = json.dumps({})
        elif name == "pr_review.json":
            content = json.dumps({"status": "pending"}) # not completed
            
        file_path.write_text(content, encoding="utf-8")
        
        # Calculate SHA256 for manifest
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        manifest[name] = {"sha256": sha}
        
    (temp_run_dir / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    
    results, is_blocked = validate_artifact_contract(temp_run_dir)
    assert is_blocked
    integrity_entry = next(x for x in results if x["status"] == "integrity_failed" and "draft_pr_integrity" in x["artifact_name"])
    assert integrity_entry["blocking"] is True

def test_frontend_backend_parity_detects_missing_route():
    # We can create a dummy app with only home route to trigger missing route validation
    app = FastAPI()
    @app.get("/")
    def read_root():
        return {}
        
    src_temp = tempfile.mkdtemp()
    try:
        src_path = Path(src_temp) / "dummy.tsx"
        # The frontend calls /api/v1/ceo/overview which does not exist in app
        src_path.write_text('safeFetchJson("/api/v1/ceo/overview")', encoding="utf-8")
        parity, is_blocked = validate_frontend_backend_parity(app, src_dir=Path(src_temp))
        assert is_blocked
        missing_entry = next(x for x in parity if x["status"] == "missing")
        assert missing_entry["blocking"] is True
    finally:
        shutil.rmtree(src_temp)

def test_release_report_status_ready_when_no_blockers(temp_run_dir):
    # Mocking app with all required routes
    app = FastAPI()
    config = load_matrix_config()
    for route_info in config.get("api_routes", []):
        path = route_info.get("route", "")
        method = route_info.get("method", "GET").upper()
        if method == "POST":
            @app.post(path)
            def dummy_post(): pass
        else:
            @app.get(path)
            def dummy_get(): pass
            
    # Mocking all required artifacts perfectly
    manifest = {}
    for schema in config.get("artifact_schemas", []):
        name = schema.get("artifact_name", "")
        file_path = temp_run_dir / name
        content = "{}"
        if name == "tournament_result.json":
            content = json.dumps({"selected_candidate_id": "cand-1"})
        elif name == "human_gate_decision.json":
            content = json.dumps({"selected_candidate_id": "cand-1", "status": "APPROVED"})
        elif name == "draft_pr_metadata.json":
            content = json.dumps({})
        elif name == "pr_review.json":
            content = json.dumps({"status": "completed"})
            
        file_path.write_text(content, encoding="utf-8")
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        manifest[name] = {"sha256": sha}
        
    (temp_run_dir / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    src_temp = tempfile.mkdtemp()
    try:
        report = build_release_readiness_report(run_dir=temp_run_dir, app=app, src_dir=Path(src_temp))
        assert report["status"] == "READY"
        assert report["blocking_count"] == 0
    finally:
        shutil.rmtree(src_temp)

def test_release_report_status_blocked_when_blockers_exist(temp_run_dir):
    app = FastAPI() # empty app -> missing critical routes
    src_temp = tempfile.mkdtemp()
    try:
        report = build_release_readiness_report(run_dir=temp_run_dir, app=app, src_dir=Path(src_temp))
        assert report["status"] == "BLOCKED"
        assert report["blocking_count"] > 0
    finally:
        shutil.rmtree(src_temp)
