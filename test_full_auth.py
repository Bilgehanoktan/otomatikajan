import requests

base_url = "http://127.0.0.1:8000/api/v1"
login_url = f"{base_url}/auth/login"
me_url = f"{base_url}/auth/me"

payload = {
    "email": "admin@sovereign.agi",
    "password": "admin1234"
}

try:
    print("Trying login...")
    session = requests.Session()
    response = session.post(login_url, json=payload)
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"Token acquired. Calling /me with Bearer token...")
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(me_url, headers=headers)
        print(f"Me (Bearer) Status: {me_response.status_code}")
        print(f"Me (Bearer) Response: {me_response.json()}")
        
        print("\nCalling /me with cookies...")
        me_cookie_response = session.get(me_url)
        print(f"Me (Cookie) Status: {me_cookie_response.status_code}")
        print(f"Me (Cookie) Response: {me_cookie_response.json()}")
    else:
        print(f"Login failed: {response.text}")
except Exception as e:
    print(f"Error: {e}")
