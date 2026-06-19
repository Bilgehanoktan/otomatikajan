import os
import pytest
from services.self_repair_audit.project_factory_readiness_scanner import ProjectFactoryReadinessScanner

def test_project_factory_readiness_missing(tmp_path):
    workspace = str(tmp_path)
    scanner = ProjectFactoryReadinessScanner(workspace)
    artifact = scanner.scan("TEST-RUN-PF-01")

    # Since all prerequisites are missing, status should be WARNING and generate findings
    assert artifact.status == "WARNING"
    assert len(artifact.findings) == 5  # 5 missing items

    pf_finding = artifact.findings[0]
    assert pf_finding.category == "project_factory"
    assert pf_finding.severity == "MEDIUM"

def test_project_factory_readiness_passed(tmp_path):
    workspace = str(tmp_path)
    
    # Create all required paths
    required_paths = [
        ("workflows/project_factory_v1.yaml", "file"),
        ("configs/project_factory_contract.yaml", "file"),
        ("generated_projects/.gitkeep", "file"),
        ("project_outputs/.gitkeep", "file"),
        ("services/project_factory/", "dir")
    ]

    for path, path_type in required_paths:
        full_path = os.path.join(workspace, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if path_type == "file":
            with open(full_path, "w") as f:
                f.write("")
        else:
            os.makedirs(full_path, exist_ok=True)

    scanner = ProjectFactoryReadinessScanner(workspace)
    artifact = scanner.scan("TEST-RUN-PF-02")

    assert artifact.status == "PASSED"
    assert len(artifact.findings) == 0
