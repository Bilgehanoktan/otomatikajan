import requests
import json
import time

# Hem root /hem de /api/v1 rootlarını test edeceğiz
URLS = ["http://localhost:8000", "http://127.0.0.1:8000"]
API_ROOT = "/api/v1"

def test_system():
    print(f"--- Sovereign AGI Kapsamli Sistem Testi Baslatiliyor ---")
    
    for base in URLS:
        print(f"\n>> TEST: {base}")
        
        # 0. Health Check (Root)
        print("  [0/4] Health Check (Root)...")
        try:
            resp = requests.get(f"{base}/health", timeout=10)
            print(f"  [OK] Health: {resp.status_code} - {resp.text[:50]}")
        except Exception as e:
            print(f"  [ERROR] Health Timeout/Error: {e}")

        # 1. Login Test
        print("  [1/4] Login Testi (admin@sovereign.agi)...")
        try:
            login_data = {"email": "admin@sovereign.agi", "password": "admin1234"}
            resp = requests.post(f"{base}{API_ROOT}/auth/login", json=login_data, timeout=10)
            if resp.status_code == 200:
                token_data = resp.json()
                access_token = token_data.get("access_token")
                print("  [OK] Login Basarili!")
                
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # 2. Auth Me Test
                print("  [2/4] Auth Me Testi...")
                resp_me = requests.get(f"{base}{API_ROOT}/auth/me", headers=headers, timeout=10)
                if resp_me.status_code == 200:
                    print(f"  [OK] Kimlik Dogrulandi: {resp_me.json()['email']}")
                else:
                    print(f"  [ERROR] Me: {resp_me.status_code}")
            else:
                print(f"  [ERROR] Login: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"  [ERROR] Login Timeout/Error: {e}")

    print("\n--- Test Tamamlandi ---")

if __name__ == "__main__":
    test_system()
