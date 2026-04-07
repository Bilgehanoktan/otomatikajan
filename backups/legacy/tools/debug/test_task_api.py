import requests
import json

url = "http://127.0.0.1:8000/api/v1/tasks"
payload = {
    "title": "Sistem Stabilite Kontrolü",
    "description": "Orkestratör ve bridge arası bağlantıyı test et.",
    "priority": "medium",
    "source": "manual",
    "tags": ["test", "stability"],
    "assigned_agent": "auto",
    "context": "Agent orkestrasyonu testi",
    "budget_limit": 5.0
}
headers = {'Content-Type': 'application/json'}

try:
    # No auth specified, but task_write_router.py has Depends(get_current_user)
    # Let's see if it works without auth (it shouldn't)
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
