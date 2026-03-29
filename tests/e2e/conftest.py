import pytest
import json
import http.server
import threading
import socket
from pathlib import Path
from playwright.sync_api import Page

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

@pytest.fixture(scope="session")
def server_port():
    return get_free_port()

@pytest.fixture(scope="session", autouse=True)
def local_server(server_port):
    """Dashboard dosyalarını sunan geçici bir web sunucusu başlatır."""
    dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dashboard_path), **kwargs)
        
        def log_message(self, format, *args):
            # Test çıktılarını kirletmemek için logları gizle
            pass

    server = http.server.HTTPServer(('localhost', server_port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://localhost:{server_port}"
    server.shutdown()

@pytest.fixture(scope="session")
def base_url(local_server):
    return local_server

@pytest.fixture(scope="function", autouse=True)
def mock_api(page: Page):
    """
    Tüm /api/v1/* isteklerini tek bir noktadan yakalar ve sahte veri döner.
    """
    import re
    dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
    
    # Tarayıcı loglarını yakalamak için (Hata ayıklama için kritik)
    page.on("console", lambda msg: print(f"BROWSER {msg.type.upper()}: {msg.text}"))
    page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err.message}"))

    def handle_route(route):
        url = route.request.url
        
        path_parts = url.split("/")
        filename = path_parts[-1].split("?")[0]
        
        # 1. Static Assets Mapping (/static/ -> dashboard/)
        if "/static/" in url:
            file_path = dashboard_path / filename
            if file_path.exists():
                with open(file_path, "rb") as f:
                    return route.fulfill(status=200, body=f.read())
            else:
                print(f"DEBUG: Static file not found -> {file_path}")

        # 2. Auth Me (CRITICAL for staying logged in)
        if "/api/v1/auth/me" in url:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "email": "test@antigravity.ai", "is_admin": True, "full_name": "Test User"
            }))

        # 3. Dashboard Stats
        if "/api/v1/tasks/stats/summary" in url:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "total": 42, "pending": 5, "running": 2, "completed": 30,
                "partial_complete": 3, "error": 2, "cost": 12.50, "is_fallback": False
            }))
        
        # 4. Monitoring Overview
        if "/api/v1/monitoring/overview" in url:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "services": {
                    "API": {"status": "online"},
                    "Worker": {"status": "online"},
                    "Redis": {"status": "online"},
                    "Database": {"status": "online"}
                },
                "metrics": {"system_score": 95, "uptime_hms": "24:12:05"},
                "queue": {"queue_size": 5, "running": 2, "completed": 150, "error": 3, "total": 160,
                          "supports_cancel": True, "supports_pause": True, "supports_resume": True}
            }))
        
        # 5. Pending Approvals
        if "/api/v1/approvals/pending" in url:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps([]))

        # 6. Budget/Finance Status
        if "/api/v1/finance/status" in url:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "spent_formatted": "$12.50", "budget_formatted": "$1,000.00", "remaining_formatted": "$987.50",
                "pct_used": 1.25, "threshold_warning": False, "over_budget": False
            }))

        # 7.1 Single Task Detail (for error verification) - MUST BE BEFORE TASKS LIST
        if "/api/v1/tasks/" in url and "stats" not in url:
             # Extract ID from end of URL
             tid = url.split("/")[-1].split("?")[0]
             return route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "id": tid, "title": "Physical E2E Test Task" if tid == "task-err" else f"Detail for {tid}", 
                "status": "error" if tid == "task-err" else "completed", "priority": "medium", "source": "manual", "progress_pct": 0, 
                "error_detail": "Görev zaman aşımına uğradı (Reaper tarafından temizlendi)." if tid == "task-err" else None, 
                "created_at": "2026-03-29T11:27:04Z", "total_cost": 0.0, "workflow_template": "default", "quality_profile": "standard",
                "logs": [], "subtasks": []
            }))

        # 7. Tasks List
        if "/api/v1/tasks" in url and "stats" not in url:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "tasks": [
                    {"id": "task-1", "title": "Mock Görev 1", "status": "completed", "priority": "high", "source": "manual", "progress_pct": 100},
                    {"id": "task-err", "title": "Physical E2E Test Task", "status": "error", "priority": "medium", "source": "manual", "progress_pct": 0, "error_detail": "Görev zaman aşımına uğradı (Reaper tarafından temizlendi)."},
                ],
                "total": 2
            }))

        # 8. Health Checks
        if "/health" in url or "/system/health" in url:
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "status": "healthy", "celery_workers": {"status": "UP"}, "telegram_bot": {"status": "UP"}
            }))

        # Yakalanmayanlar için normal devam et
        # print(f"DEBUG MISS: {url}")
        route.continue_()

    # Tüm API ve Static çağrılarını yakala
    page.route(re.compile(r".*(/api/v1/|/static/|/health).*"), handle_route)
    yield
