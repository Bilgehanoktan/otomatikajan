import pytest

from services.ui_repair import runtime_guard


def test_runtime_guard_normalizes_windows_browser_path_inside_container(monkeypatch):
    monkeypatch.setattr(runtime_guard.os.path, "exists", lambda path: path == "/.dockerenv")
    monkeypatch.setenv("DOCKER_CONTAINER", "true")
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", r"C:\Users\BILGEHAN\.gemini\antigravity\.playwright-browsers")

    previous = runtime_guard._normalize_playwright_browser_path()

    assert previous == r"C:\Users\BILGEHAN\.gemini\antigravity\.playwright-browsers"
    assert runtime_guard.os.getenv("PLAYWRIGHT_BROWSERS_PATH") == "/ms-playwright"


def test_runtime_guard_keeps_valid_container_browser_path(monkeypatch):
    monkeypatch.setattr(runtime_guard.os.path, "exists", lambda path: path == "/.dockerenv")
    monkeypatch.setenv("DOCKER_CONTAINER", "true")
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", "/ms-playwright")

    previous = runtime_guard._normalize_playwright_browser_path()

    assert previous is None
    assert runtime_guard.os.getenv("PLAYWRIGHT_BROWSERS_PATH") == "/ms-playwright"


def test_runtime_guard_repairs_invalid_windows_host_browser_path(monkeypatch):
    valid_host_cache = r"C:\Users\BILGEHAN\.gemini\antigravity\.playwright-browsers"

    def fake_exists(path):
        return path.replace("\\", "/").rstrip("/") == valid_host_cache.replace("\\", "/").rstrip("/")

    monkeypatch.setattr(runtime_guard.os.path, "exists", fake_exists)
    monkeypatch.setattr(runtime_guard.os.path, "expanduser", lambda _: r"C:\Users\BILGEHAN")
    monkeypatch.delenv("DOCKER_CONTAINER", raising=False)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", r"C:\Users\BLGEHA~1\.gemini\antigravity\.playwright-browsers")

    previous = runtime_guard._normalize_playwright_browser_path()

    assert previous == r"C:\Users\BLGEHA~1\.gemini\antigravity\.playwright-browsers"
    assert runtime_guard.os.getenv("PLAYWRIGHT_BROWSERS_PATH").replace("\\", "/") == valid_host_cache.replace("\\", "/")


@pytest.mark.asyncio
async def test_runtime_guard_treats_docker_as_optional_for_smoke(monkeypatch):
    async def ok_playwright():
        return {"available": True}

    async def missing_docker():
        return {
            "available": False,
            "reason": "docker_not_installed",
            "operator_action": "Install Docker Desktop for sandboxed agent operations.",
            "error_details": "Docker executable not found on path.",
        }

    monkeypatch.setattr(runtime_guard, "check_playwright", ok_playwright)
    monkeypatch.setattr(runtime_guard, "check_llm", lambda: {"available": True, "active_providers": ["mock"]})
    monkeypatch.setattr(runtime_guard, "check_docker", missing_docker)
    monkeypatch.setattr(runtime_guard, "check_db", lambda: {"available": True, "degraded": False})

    result = await runtime_guard.check_runtime_dependencies(require_docker=False)

    assert result["status"] == "healthy"
    assert result["details"]["docker"]["available"] is False
    assert result["details"]["docker"]["required"] is False
    assert result["warnings"][0]["stage"] == "sandboxed_execution"


@pytest.mark.asyncio
async def test_runtime_guard_blocks_when_docker_is_required(monkeypatch):
    async def ok_playwright():
        return {"available": True}

    async def missing_docker():
        return {
            "available": False,
            "reason": "docker_not_installed",
            "operator_action": "Install Docker Desktop for sandboxed agent operations.",
            "error_details": "Docker executable not found on path.",
        }

    monkeypatch.setattr(runtime_guard, "check_playwright", ok_playwright)
    monkeypatch.setattr(runtime_guard, "check_llm", lambda: {"available": True, "active_providers": ["mock"]})
    monkeypatch.setattr(runtime_guard, "check_docker", missing_docker)
    monkeypatch.setattr(runtime_guard, "check_db", lambda: {"available": True, "degraded": False})

    result = await runtime_guard.check_runtime_dependencies(require_docker=True)

    assert result["status"] == "degraded"
    assert result["reason"] == "docker_not_installed"
    assert result["failed_stage"] == "sandboxed_execution"
