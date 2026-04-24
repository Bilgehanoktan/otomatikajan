import requests

def check(url):
    print(f"Checking {url}...")
    try:
        r = requests.get(url)
        print(f"  Status: {r.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

check("http://localhost:8000/api/v1/governance/proposals?status=pending")
