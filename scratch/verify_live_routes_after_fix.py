from fastapi.testclient import TestClient
from services.workflow_api.main import app

client = TestClient(app)
checks = [
    ("GET", "/api/v1/workflows/stats/summary"),
    ("GET", "/api/v1/health/dashboard"),
    ("GET", "/api/v1/workflows?_end=10&_order=desc&_sort=started_at&_start=0"),
    ("GET", "/api/v1/ui-repair/governance/overrides"),
    ("POST", "/api/v1/repair-lab/cases/UI-RUN-CHECK/trigger-autonomous-repair?target_url=http%3A%2F%2Flocalhost%3A3100%2Frepair-lab"),
]
for method, url in checks:
    resp = client.request(method, url, json={})
    print(method, url, resp.status_code, resp.text[:220].replace("\n", " "))
