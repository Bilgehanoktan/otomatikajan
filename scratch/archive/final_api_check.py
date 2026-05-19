import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    print(f"Testing {method} {url}...", end=" ")
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=data, timeout=5)
        
        # 422 is OK for some POST tests where we purposely omit complex fields but check route existence
        if r.status_code < 400 or (r.status_code == 422 and method == "POST"):
            print("OK")
            return True
        else:
            print(f"FAILED ({r.status_code})")
            print(f"Response: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def run_suite():
    print("--- Sovereign AGI API Validation Suite ---")
    
    # Core Infrastructure
    test_endpoint("/health")
    test_endpoint("/api/v1/fleet/projects")
    test_endpoint("/api/v1/mesh/status")
    test_endpoint("/api/v1/metrics/phase17")
    
    # Governance Control Plane
    test_endpoint("/api/v1/approvals")
    test_endpoint("/api/v1/improvements")
    test_endpoint("/api/v1/federation/trust")
    
    # Repair Lab & Self-Tuning
    test_endpoint("/api/v1/repair-lab/benchmarks")
    test_endpoint("/api/v1/repair-lab/suggestions")
    test_endpoint("/api/v1/repair-lab/dashboard")
    test_endpoint("/api/v1/repair-lab/verifiers")

    print("-" * 40)

if __name__ == "__main__":
    run_suite()
