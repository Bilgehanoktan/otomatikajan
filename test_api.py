
import requests

def test_endpoint(url):
    try:
        resp = requests.get(url)
        print(f"URL: {url} | Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"URL: {url} | Error: {e}")

base = "http://127.0.0.1:8000/api/v1"
test_endpoint(f"{base}/evolution/state")
test_endpoint(f"{base}/compliance/policies")
test_endpoint(f"{base}/governance/status")
