import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

endpoints = [
    ("/health", "Health Status"),
    ("/api/v1/workflows", "Workflows List"),
    ("/api/v1/incidents", "Operational Incidents"),
    ("/api/v1/approvals", "Pending Approvals"),
    ("/api/v1/fleet/status", "Fleet Statistics"),
    ("/api/v1/fleet/projects", "Fleet Projects Heatmap"),
    ("/api/v1/compliance/audit-bundles", "Audit Bundles"),
    ("/api/v1/ops/launch-gates", "Launch Gatekeeper Status"),
]

def test_system():
    print(f"--- Sovereign AGI Control Plane Verification ---")
    print(f"Backend: {BASE_URL}\n")
    
    all_passed = True
    
    for path, name in endpoints:
        url = f"{BASE_URL}{path}" if not path.startswith("http") else path
        try:
            resp = requests.get(url, timeout=5)
            status = resp.status_code
            if status == 200:
                print(f"[OK]   {name:<30} ({path})")
            else:
                print(f"[FAIL] {name:<30} ({path}) - Status: {status}")
                all_passed = False
        except Exception as e:
            print(f"[ERR]  {name:<30} ({path}) - Exception: {str(e)}")
            all_passed = False
            
    print(f"\n--- Result: {'SUCCESS' if all_passed else 'FAILURE'} ---")
    return all_passed

if __name__ == "__main__":
    if not test_system():
        sys.exit(1)
