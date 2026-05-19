import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_repair_lab():
    print("Checking Repair Lab endpoints...")
    
    # 1. Benchmarks
    try:
        resp = requests.get(f"{BASE_URL}/repair-lab/benchmarks")
        print(f"Benchmarks Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Benchmarks count: {len(data)}")
            if len(data) > 0:
                print(f"First benchmark: {data[0].get('name')}")
    except Exception as e:
        print(f"Benchmarks Error: {e}")

    # 2. Tournaments
    try:
        resp = requests.get(f"{BASE_URL}/repair-lab/tournaments")
        print(f"Tournaments Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Tournaments count: {len(data)}")
    except Exception as e:
        print(f"Tournaments Error: {e}")

if __name__ == "__main__":
    check_repair_lab()
