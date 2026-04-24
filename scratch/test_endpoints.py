
import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_endpoint(endpoint):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {url}...")
    try:
        response = requests.get(url)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Count: {len(data) if isinstance(data, list) else 'Object'}")
            # print(f"  Sample: {json.dumps(data[:1], indent=2) if isinstance(data, list) and data else 'N/A'}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  Connection Failed: {e}")

def test_patch(endpoint, payload):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing PATCH {url}...")
    try:
        response = requests.patch(url, json=payload)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  Connection Failed: {e}")

# List tests
test_endpoint("/approvals")
test_endpoint("/incidents")
test_endpoint("/improvements")
test_endpoint("/self-tuning")
test_endpoint("/verifiers")
test_endpoint("/repair-memory")

# Find an approval to patch
try:
    approvals = requests.get(f"{BASE_URL}/approvals").json()
    if approvals:
        aid = approvals[0]['id']
        test_patch(f"/approvals/{aid}", {"approve": True, "reason": "Test approval", "decided_by": "Operator-Test"})
except:
    print("Could not find approval to test PATCH")
