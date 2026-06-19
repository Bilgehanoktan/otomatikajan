import pytest
from services.project_factory.pr_safety import validate_pr_creation_safety

def test_validate_pr_creation_safety_missing_operator(monkeypatch):
    with pytest.raises(ValueError, match="operator_id is required"):
        validate_pr_creation_safety("PF-1", "", "rationale", True, "root")

def test_validate_pr_creation_safety_missing_rationale(monkeypatch):
    with pytest.raises(ValueError, match="valid rationale"):
        validate_pr_creation_safety("PF-1", "op", "", True, "root")

def test_validate_pr_creation_safety_no_risk_ack(monkeypatch):
    with pytest.raises(ValueError, match="acknowledge risks"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", False, "root")

def test_validate_pr_creation_safety_validates_manifest(monkeypatch):
    monkeypatch.setattr("services.project_factory.pr_safety.load_delivery_manifest", lambda p, r: None)
    with pytest.raises(ValueError, match="No delivery_manifest"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")
        
    monkeypatch.setattr("services.project_factory.pr_safety.load_delivery_manifest", lambda p, r: {"production_apply_allowed": True})
    with pytest.raises(ValueError, match="production_apply_allowed must strictly be False"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")

def test_validate_pr_creation_safety_validates_preview(monkeypatch):
    monkeypatch.setattr("services.project_factory.pr_safety.load_delivery_manifest", lambda p, r: {"production_apply_allowed": False})
    
    monkeypatch.setattr("services.project_factory.pr_safety.load_apply_preview", lambda p, r: None)
    with pytest.raises(ValueError, match="Missing apply_preview.json"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")

    monkeypatch.setattr("services.project_factory.pr_safety.load_apply_preview", lambda p, r: {"blocking_risks": ["secret_found"]})
    with pytest.raises(ValueError, match="contains blocking risks"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")
        
    monkeypatch.setattr("services.project_factory.pr_safety.load_apply_preview", lambda p, r: {"blocking_risks": [], "production_apply_performed": True})
    with pytest.raises(ValueError, match="production apply was already performed"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")

def test_validate_pr_creation_safety_validates_plan(monkeypatch):
    monkeypatch.setattr("services.project_factory.pr_safety.load_delivery_manifest", lambda p, r: {"production_apply_allowed": False})
    monkeypatch.setattr("services.project_factory.pr_safety.load_apply_preview", lambda p, r: {"blocking_risks": [], "production_apply_performed": False})
    
    monkeypatch.setattr("services.project_factory.pr_safety.load_draft_pr_plan", lambda p, r: None)
    with pytest.raises(ValueError, match="Missing draft_pr_plan.json"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")
        
    monkeypatch.setattr("services.project_factory.pr_safety.load_draft_pr_plan", lambda p, r: {"branch_name": "feature/123", "target_branch": "main"})
    with pytest.raises(ValueError, match="branch_name must start with 'codex/'"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")

    monkeypatch.setattr("services.project_factory.pr_safety.load_draft_pr_plan", lambda p, r: {"branch_name": "codex/feature", "target_branch": "develop"})
    with pytest.raises(ValueError, match="target_branch must be main or master"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")

def test_validate_pr_creation_safety_success(monkeypatch):
    monkeypatch.setattr("services.project_factory.pr_safety.load_delivery_manifest", lambda p, r: {"production_apply_allowed": False})
    monkeypatch.setattr("services.project_factory.pr_safety.load_apply_preview", lambda p, r: {"blocking_risks": [], "production_apply_performed": False})
    monkeypatch.setattr("services.project_factory.pr_safety.load_draft_pr_plan", lambda p, r: {"branch_name": "codex/PF-1", "target_branch": "main", "files_to_apply": ["a.txt"]})
    
    res = validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")
    assert res["draft_pr_plan"]["branch_name"] == "codex/PF-1"
