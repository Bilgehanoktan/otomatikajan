import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_sif_protection():
    print("--- SIF-01 Advanced Backend Stress Test ---")
    
    # 1. Login as Prime
    print("\n[*] Scenario 1: Prime Operator Login")
    login_data = {"email": "admin@sovereign.agi", "password": "admin1234"}
    res = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if res.status_code == 200:
        print("[SUCCESS] Prime login OK.")
        token = res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Try an Authorized Write Action (Incident Resolve)
        # Using a dummy ID to see if we get 404 (Auth passed) or 403 (Auth failed)
        print("\n[*] Scenario 2: Authorized Write Action (Incident Resolve)")
        res_write = requests.post(
            f"{BASE_URL}/incidents/fake-id/resolve", 
            json={"resolution_notes": "test", "operator_id": "admin"},
            headers=auth_headers
        )
        print(f"[STATUS] {res_write.status_code} (Expect 404/200, NOT 403)")
    else:
        print(f"[FAILED] Login failed: {res.text}")

    # 3. Try with Invalid API KEY (No JWT)
    print("\n[*] Scenario 3: Invalid API KEY Access (Protected Route)")
    headers_bad_api = {"X-API-KEY": "wrong-key-123"}
    res_bad = requests.post(
        f"{BASE_URL}/incidents/fake-id/resolve", 
        json={"resolution_notes": "test", "operator_id": "admin"},
        headers=headers_bad_api
    )
    print(f"[STATUS] {res_bad.status_code} (Expect 401)")

    # 4. Try with NO AUTH
    print("\n[*] Scenario 4: No Auth Access")
    res_none = requests.post(
        f"{BASE_URL}/incidents/fake-id/resolve", 
        json={"resolution_notes": "test", "operator_id": "admin"}
    )
    print(f"[STATUS] {res_none.status_code} (Expect 401)")

if __name__ == "__main__":
    test_sif_protection()
