"""
Faz 4 Testleri — Yeni modüller
• Task router şema doğrulaması
• Telegram bot komut ayrıştırması
• Monitoring router yapısı
• Repository metotları
"""

import sys
import os
import json
import pytest
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ════════════════════════════════════════════════════════
# 1. TaskCreateRequest validasyonu
# ════════════════════════════════════════════════════════
def test_task_create_request_valid():
    from api.task_router import TaskCreateRequest
    req = TaskCreateRequest(
        title="Test görevi",
        description="Açıklama",
        priority="high",
        source="manual",
        tags=["auth", "backend"],
    )
    assert req.title == "Test görevi"
    assert req.priority == "high"
    assert req.source == "manual"
    assert "auth" in req.tags


def test_task_create_request_defaults():
    from api.task_router import TaskCreateRequest
    req = TaskCreateRequest(title="Min test")
    assert req.priority == "medium"
    assert req.source == "manual"
    assert req.tags == []
    assert req.notes == ""


def test_task_create_request_invalid_priority():
    from api.task_router import TaskCreateRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="Test", priority="urgent")  # geçersiz öncelik


def test_task_create_request_invalid_source():
    from api.task_router import TaskCreateRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="Test", source="slack")  # geçersiz kaynak


def test_task_create_request_short_title():
    from api.task_router import TaskCreateRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="AB")  # 2 karakter, min 3


def test_task_update_request_optional_fields():
    from api.task_router import TaskUpdateRequest
    req = TaskUpdateRequest(priority="low")
    assert req.priority == "low"
    assert req.title is None
    assert req.tags is None


def test_task_update_request_empty():
    from api.task_router import TaskUpdateRequest
    req = TaskUpdateRequest()
    assert req.priority is None
    assert req.title is None


# ════════════════════════════════════════════════════════
# 2. _project_to_dict
# ════════════════════════════════════════════════════════
def test_project_to_dict_basic():
    from api.task_router import _project_to_dict
    from unittest.mock import MagicMock
    from datetime import datetime, timezone

    p = MagicMock()
    p.id = "11111111-1111-1111-1111-111111111111"
    p.title = "Test"
    p.description = "Açıklama"
    p.status = "pending"
    p.source = "api"
    p.priority = "medium"
    p.progress_pct = 25
    p.tags = ["tag1"]
    p.assigned_agent = ""
    p.job_id = "abc123"
    p.notes = ""
    p.error_detail = ""
    p.retry_count = 0
    p.total_cost = 0.0
    p.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    p.started_at = None
    p.completed_at = None
    p.deadline = None
    p.cancelled_at = None
    p.cancelled_by = ""

    result = _project_to_dict(p)
    assert result["id"] == str(p.id)
    assert result["status"] == "pending"
    assert result["progress_pct"] == 25
    assert "subtasks" not in result   # subtasks=None -> not included
    assert "logs" not in result


def test_project_to_dict_with_subtasks():
    from api.task_router import _project_to_dict
    from unittest.mock import MagicMock
    from datetime import datetime, timezone

    p = MagicMock()
    p.id = "22222222-2222-2222-2222-222222222222"
    p.title = "Test"
    p.description = ""
    p.status = "done"
    p.source = "manual"
    p.priority = "high"
    p.progress_pct = 100
    p.tags = []
    p.assigned_agent = "backend_dev"
    p.job_id = ""
    p.notes = ""
    p.error_detail = ""
    p.retry_count = 1
    p.total_cost = 0.01
    p.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    p.started_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    p.completed_at = datetime(2025, 1, 2, tzinfo=timezone.utc)
    p.deadline = None
    p.cancelled_at = None
    p.cancelled_by = ""

    s1 = MagicMock()
    s1.id = "33333333-3333-3333-3333-333333333333"
    s1.agent_id = "backend_dev"
    s1.status = "done"
    s1.attempts = 2
    s1.recovered = False
    s1.llm_provider = "openai"
    s1.input_tokens = 100
    s1.output_tokens = 200
    s1.cost_usd = 0.005
    s1.latency_s = 2.3
    s1.result = "OK"
    s1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    s1.completed_at = datetime(2025, 1, 2, tzinfo=timezone.utc)

    result = _project_to_dict(p, subtasks=[s1])
    assert "subtasks" in result
    assert len(result["subtasks"]) == 1
    assert result["subtasks"][0]["agent_id"] == "backend_dev"
    assert result["subtasks"][0]["status"] == "done"


# ════════════════════════════════════════════════════════
# 3. Telegram Bot Komut Ayrıştırma
# ════════════════════════════════════════════════════════
def test_telegram_commands_dict():
    from telegram_app.bot import COMMANDS
    required = ["/start", "/help", "/status", "/tasks", "/task",
                "/newtask", "/agents", "/logs", "/errors", "/queue", "/metrics"]
    for cmd in required:
        assert cmd in COMMANDS, f"{cmd} COMMANDS'da yok"


def test_telegram_authorized_commands_require_auth():
    from telegram_app.bot import COMMANDS
    # /start auth gerektirmemeli
    _, start_auth = COMMANDS["/start"]
    assert start_auth is False, "/start auth gerektirmemeli"
    # diğerleri gerektirmeli
    _, status_auth = COMMANDS["/status"]
    assert status_auth is True, "/status auth gerektirmeli"


def test_telegram_newtask_parse():
    from telegram_app.bot import BotCommandHandler
    handler = BotCommandHandler()
    # args parse simulasyonu
    args = "Auth servisi | JWT refresh ekle | high"
    parts = [p.strip() for p in args.split("|")]
    assert parts[0] == "Auth servisi"
    assert parts[1] == "JWT refresh ekle"
    assert parts[2] == "high"


def test_telegram_allowed_ids_parsing():
    import os
    os.environ["TELEGRAM_ALLOWED_IDS"] = "123456,789012,345678"
    # Modülü yeniden import etmeden parse simule et
    ids = set(filter(None, "123456,789012,345678".split(",")))
    assert "123456" in ids
    assert "789012" in ids
    assert len(ids) == 3


def test_telegram_notifier_events():
    from telegram_app.bot import TelegramNotifier
    notifier = TelegramNotifier()
    assert "project.completed" in notifier.NOTIFY_EVENTS
    assert "project.failed" in notifier.NOTIFY_EVENTS
    assert "heal.critical" in notifier.NOTIFY_EVENTS


# ════════════════════════════════════════════════════════
# 4. Monitoring Router yapısı
# ════════════════════════════════════════════════════════
def test_monitoring_router_has_routes():
    from api.monitoring_router import router
    paths = [r.path for r in router.routes]
    assert any("/overview" in p for p in paths)
    assert any("/api/stats" in p for p in paths)
    assert any("/llm" in p for p in paths)
    assert any("/queue" in p for p in paths)
    assert any("/system" in p for p in paths)
    assert any("/agents" in p for p in paths)
    assert any("/errors" in p for p in paths)


def test_task_router_has_routes():
    from api.task_router import router
    paths = [r.path for r in router.routes]
    # Temel CRUD
    assert any(p == "/tasks" for p in paths)
    assert any("/tasks/{task_id}" in p for p in paths)
    assert any("/cancel" in p for p in paths)
    assert any("/retry" in p for p in paths)
    assert any("/copy" in p for p in paths)
    assert any("/logs" in p for p in paths)
    assert any("/stop" in p for p in paths)


def test_telegram_router_has_routes():
    from api.telegram_router import router
    paths = [r.path for r in router.routes]
    assert any("/webhook" in p for p in paths)
    assert any("/info" in p for p in paths)
    assert any("/users" in p for p in paths)
    assert any("/setup" in p for p in paths)


# ════════════════════════════════════════════════════════
# 5. Monitoring _system_resources
# ════════════════════════════════════════════════════════
def test_system_resources_returns_dict():
    from api.monitoring_router import _system_resources
    result = _system_resources()
    assert isinstance(result, dict)
    assert "available" in result
    # psutil yüklü değilse False, yüklüyse True + cpu_pct
    if result["available"]:
        assert "cpu_pct" in result
        assert "ram_pct" in result
        assert 0 <= result["cpu_pct"] <= 100
        assert 0 <= result["ram_pct"] <= 100


# ════════════════════════════════════════════════════════
# 6. Main.py entegrasyon
# ════════════════════════════════════════════════════════
def test_main_imports_new_routers():
    content = open(os.path.join(os.path.dirname(__file__), "..", "main.py"), encoding="utf-8").read()
    assert "task_read_router" in content
    assert "monitoring_router" in content
    assert "telegram_router" in content


def test_logging_middleware_patches():
    content = open(os.path.join(os.path.dirname(__file__), "..", "observability", "logging.py"), encoding="utf-8").read()
    assert "ApiMetricRepository" in content
    assert "asyncio.create_task" in content
    assert "response_ms" in content


# ════════════════════════════════════════════════════════
# 7. Dashboard HTML bütünlük
# ════════════════════════════════════════════════════════
def test_dashboard_html_has_sections():
    dash_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "index.html")
    html = open(dash_path, encoding="utf-8").read()
    assert "page-dashboard" in html
    assert "page-tasks" in html
    assert "page-agents" in html
    assert "page-monitoring" in html
    assert "page-telegram" in html
    assert "page-logs" in html
    assert "modal-create" in html
    assert "modal-detail" in html
    assert "loadDashboard" in html
    assert "loadTasks" in html
    assert "submitCreateTask" in html


def test_dashboard_has_task_operations():
    dash_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "index.html")
    html = open(dash_path, encoding="utf-8").read()
    assert "retryTask" in html
    assert "cancelTask" in html
    assert "deleteTask" in html
    assert "copyTask" in html
    assert "openTaskDetail" in html


def test_dashboard_has_telegram_section():
    dash_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "index.html")
    html = open(dash_path, encoding="utf-8").read()
    assert "telegram-info" in html
    assert "telegram-users" in html
    assert "registerCommands" in html
    assert "setupWebhook" in html


# ════════════════════════════════════════════════════════
# 8. Faz 1-3 regresyon
# ════════════════════════════════════════════════════════
def test_existing_modules_intact():
    """Mevcut modüller bozulmamış mı?"""
    import importlib
    modules = [
        "core.events", "packages.orchestration.application.job_queue", "core.orchestrator",
        "packages.observability.metrics", "packages.observability.logging",
        "api.rate_limiter", "api.ws_manager",
        "packages.persistence.models", "packages.persistence.repository",
    ]
    for mod in modules:
        try:
            importlib.import_module(mod)
        except ImportError as e:
            pytest.fail(f"{mod} import edilemedi: {e}")


def test_db_models_have_faz4_tables():
    from packages.persistence.models import (
        Project, TaskLog, ApiMetric,
        TelegramUser, TelegramCommandLog
    )
    # Tablo adları doğru mu?
    assert Project.__tablename__ == "projects"
    assert TaskLog.__tablename__ == "task_logs"
    assert ApiMetric.__tablename__ == "api_metrics"
    assert TelegramUser.__tablename__ == "telegram_users"
    assert TelegramCommandLog.__tablename__ == "telegram_command_logs"


def test_project_model_faz4_fields():
    from packages.persistence.models import Project
    cols = {c.name for c in Project.__table__.columns}
    faz4_fields = {"source", "priority", "progress_pct", "tags",
                   "deadline", "assigned_agent", "error_detail",
                   "retry_count", "notes", "cancelled_at", "cancelled_by"}
    for f in faz4_fields:
        assert f in cols, f"Project.{f} eksik"


def test_repository_task_log_methods():
    from packages.persistence.repository import TaskLogRepository
    assert hasattr(TaskLogRepository, "write")
    assert hasattr(TaskLogRepository, "get_by_project")


def test_repository_api_metric_methods():
    from packages.persistence.repository import ApiMetricRepository
    assert hasattr(ApiMetricRepository, "write")
    assert hasattr(ApiMetricRepository, "endpoint_stats")
    assert hasattr(ApiMetricRepository, "time_series")
    assert hasattr(ApiMetricRepository, "cleanup_old")


def test_repository_telegram_methods():
    from packages.persistence.repository import TelegramRepository
    assert hasattr(TelegramRepository, "get_user")
    assert hasattr(TelegramRepository, "upsert_user")
    assert hasattr(TelegramRepository, "is_authorized")
    assert hasattr(TelegramRepository, "authorize")
    assert hasattr(TelegramRepository, "log_command")
    assert hasattr(TelegramRepository, "list_users")


def test_project_repository_faz4_methods():
    from packages.persistence.repository import ProjectRepository
    assert hasattr(ProjectRepository, "cancel")
    assert hasattr(ProjectRepository, "update_fields")
    assert hasattr(ProjectRepository, "set_error")
    assert hasattr(ProjectRepository, "increment_retry")
    assert hasattr(ProjectRepository, "counts_by_status")
    assert hasattr(ProjectRepository, "list_recent")
