
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_endpoint(name, path, method="GET", body=None):
    url = f"{BASE_URL}{path}"
    print(f"Testing {name}: {method} {url}...")
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=body, timeout=5)
        
        if response.status_code == 200:
            print(f"  [OK] {name} returned 200")
            # print(f"  Data: {json.dumps(response.json(), indent=2)[:200]}...")
            return True, response.json()
        else:
            print(f"  [FAIL] {name} returned {response.status_code}")
            print(f"  Error: {response.text}")
            return False, response.text
    except Exception as e:
        print(f"  [ERROR] {name} failed: {e}")
        return False, str(e)

def run_suite():
    results = {}
    
    # 1. Health check (No auth)
    results["health"] = test_endpoint("Health", "/health")
    
    # 2. Fleet Metrics
    results["fleet_metrics"] = test_endpoint("Fleet Metrics", "/fleet/metrics")
    
    # 3. Fleet Agents
    results["fleet_agents"] = test_endpoint("Fleet Agents", "/fleet/agents")
    
    # 4. Governance Status
    results["governance_status"] = test_endpoint("Governance Status", "/governance/status")
    
    # 5. Governor Status
    # Note: These might fail if the endpoints require JWT auth and we haven't logged in.
    # But some might be open or we can see the 401 as a "correct" response for auth enforcement.
    results["governor_status"] = test_endpoint("Governor Status", "/governance/governor/status")
    
    print("\n--- TEST SUMMARY ---")
    all_ok = True
    for name, (ok, _) in results.items():
        status = "PASSED" if ok else "FAILED (Expected if Auth required)"
        print(f"{name}: {status}")
        if not ok: all_ok = False
    
    with open("apps/public_api/test_results.json", "w") as f:
        json.dump({k: v[1] if v[0] else str(v[1]) for k, v in results.items()}, f, indent=2)
    print("\nResults saved to apps/public_api/test_results.json")

if __name__ == "__main__":
    run_suite()
