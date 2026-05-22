import os
import pytest
from services.self_repair_audit.api_contract_scanner import APIContractScanner

def test_api_contract_scanner_detection(tmp_path):
    # Setup dummy directory structure
    workspace = str(tmp_path)
    frontend_dir = os.path.join(workspace, "apps", "refine_control_plane", "src")
    backend_dir = os.path.join(workspace, "services", "workflow_api")
    
    os.makedirs(frontend_dir, exist_ok=True)
    os.makedirs(backend_dir, exist_ok=True)

    # 1. Frontend file with various api calls:
    # - Route A: /api/v1/ui-repair/governance/overrides with GET (Method mismatch)
    # - Route B: /api/v1/missing-endpoint with POST (Missing route)
    # - Route C: /api/v1/ok-endpoint with GET (Should match backend)
    frontend_code = """
    import axios from 'axios';
    
    async function test() {
        // Method Mismatch (Backend defines POST)
        const resA = await axios.get('/api/v1/ui-repair/governance/overrides');
        
        // Missing Route entirely
        const resB = await axios.post('/api/v1/missing-endpoint');
        
        // OK Route
        const resC = await axios.get('/api/v1/ok-endpoint');
    }
    """
    
    with open(os.path.join(frontend_dir, "test_page.tsx"), "w", encoding="utf-8") as f:
        f.write(frontend_code)

    # 2. Backend files:
    # - Route A defines POST /api/v1/ui-repair/governance/overrides
    # - Route C defines GET /api/v1/ok-endpoint
    backend_code = """
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.post("/api/v1/ui-repair/governance/overrides")
    def post_override():
        return {}
        
    @router.get("/api/v1/ok-endpoint")
    def get_ok():
        return {}
    """
    
    with open(os.path.join(backend_dir, "router.py"), "w", encoding="utf-8") as f:
        f.write(backend_code)

    # Run Scanner
    scanner = APIContractScanner(workspace)
    artifact = scanner.scan("TEST-RUN-001")

    # Assertions
    assert artifact.audit_run_id == "TEST-RUN-001"
    assert artifact.scanner == "api_contract_scanner"
    assert artifact.status == "FAILED"  # Due to HIGH severity findings

    findings = artifact.findings
    assert len(findings) == 2  # One method mismatch, one missing route

    # Find the missing route finding
    missing_finding = next((f for f in findings if "Missing API Route" in f.title), None)
    assert missing_finding is not None
    assert "/api/v1/missing-endpoint" in missing_finding.description
    assert missing_finding.severity == "HIGH"
    assert missing_finding.category == "api_contract"

    # Find the method mismatch finding
    mismatch_finding = next((f for f in findings if "API Method Mismatch" in f.title), None)
    assert mismatch_finding is not None
    assert "/api/v1/ui-repair/governance/overrides" in mismatch_finding.description
    assert "supports: POST" in mismatch_finding.description
    assert mismatch_finding.severity == "HIGH"
