import requests

url = "http://127.0.0.1:8000/api/v1/auth/login"
payload = {
    "email": "admin@sovereign.agi",
    "password": "admin1234"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
