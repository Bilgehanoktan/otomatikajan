from __future__ import annotations

import os
import shutil
import pytest
from pathlib import Path
from services.project_factory.candidate_packager import package_candidate, load_candidate_manifest
from services.project_factory.artifacts import _resolve_project_dir

WORKSPACE_ROOT = Path("e:/ai_company_faz12.1").resolve()
TEST_PROJECT_ID = "PF-TEST-PKG-888"
TEST_PROJECT_DIR = WORKSPACE_ROOT / "project_outputs" / "project_factory" / TEST_PROJECT_ID

@pytest.fixture(autouse=True)
def setup_test_project():
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)
    TEST_PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Scaffold a mock sandbox file
    sandbox_dir = TEST_PROJECT_DIR / "sandbox"
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    with open(sandbox_dir / "README.md", "w", encoding="utf-8") as f:
        f.write("# Hello Sandbox")
        
    yield
    
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)

def test_package_candidate_success():
    manifest = package_candidate(
        project_id=TEST_PROJECT_ID,
        template_name="documentation-pack",
        verification_status="PASSED",
        test_commands=[],
        workspace_root=str(WORKSPACE_ROOT)
    )
    
    assert manifest["project_id"] == TEST_PROJECT_ID
    assert manifest["status"] == "CANDIDATE_READY"
    assert manifest["requires_human_gate"] is True
    
    # Check package folder
    cand_dir = TEST_PROJECT_DIR / "candidate_package"
    assert cand_dir.exists()
    assert (cand_dir / "README.md").exists()
    
    # Load manifest from disk
    loaded = load_candidate_manifest(TEST_PROJECT_ID, str(WORKSPACE_ROOT))
    assert loaded is not None
    assert loaded["candidate_id"] == manifest["candidate_id"]
