from fastapi.testclient import TestClient
from services.workflow_api.main import app

client = TestClient(app, raise_server_exceptions=True)
for url in ['/api/v1/workflows/stats/summary','/api/v1/health/dashboard','/api/v1/workflows?_end=10&_order=desc&_sort=started_at&_start=0']:
    print('\n===', url)
    try:
        r = client.get(url)
        print(r.status_code, r.text[:500])
    except Exception:
        import traceback
        traceback.print_exc()
