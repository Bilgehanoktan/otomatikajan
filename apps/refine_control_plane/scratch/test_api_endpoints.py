import requests

def test_api():
    base_url = "http://localhost:8000/api/v1"
    endpoints = [
        "/memory/heatmaps",
        "/learning/insights",
        "/governance/inbox/governor/metrics",
        "/governance/inbox/governor/alerts",
        "/governance/inbox/governor/resilience/drills"
    ]
    
    for ep in endpoints:
        url = f"{base_url}{ep}"
        try:
            # Authorized Degraded mode might require some auth, 
            # but let's check if the route exists (not 404)
            resp = requests.get(url, timeout=5)
            print(f"GET {url} -> Status: {resp.status_code}")
        except Exception as e:
            print(f"GET {url} -> Error: {str(e)}")

if __name__ == "__main__":
    test_api()
