import requests
import json
import sys

def test_api(workflow_id):
    url = f"http://localhost:8000/api/v1/workflows/{workflow_id}/"
    print(f"Testing URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print("Headers:", response.headers)
        try:
            print("Content:", json.dumps(response.json(), indent=2))
        except:
            print("Content (raw):", response.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    workflow_id = "6bf72fb5-7cd8-4d9e-b928-54af95867c64"
    test_api(workflow_id)
