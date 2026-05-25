import asyncio
import os
import subprocess
from typing import Dict, Any, List
from services.observability.logging import get_logger

_log = get_logger("ui_repair_runtime_guard")

async def check_playwright() -> Dict[str, Any]:
    """Checks if Playwright is installed and the Chromium binary is available."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        clean_err = str(e).encode('ascii', 'ignore').decode('ascii')
        _log.warning(f"Playwright package is not installed: {clean_err}")
        return {
            "available": False,
            "reason": "playwright_package_missing",
            "operator_action": "py -3.13 -m pip install playwright",
            "error_details": clean_err
        }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
        return {"available": True}
    except Exception as e:
        clean_err = str(e).encode('ascii', 'ignore').decode('ascii')
        _log.warning(f"Playwright Chromium browser binary is not available or failed: {clean_err}")
        return {
            "available": False,
            "reason": "playwright_browser_unavailable",
            "operator_action": "py -3.13 -m playwright install chromium",
            "error_details": clean_err
        }

def check_llm() -> Dict[str, Any]:
    """Checks if at least one LLM provider has a non-placeholder API key and is available."""
    try:
        from libs.llm.model_orchestrator import PROVIDERS
        active_providers = []
        for provider in PROVIDERS:
            # Check availability (quarantine, circuit states) and if key is placeholder
            if provider.is_available() and not provider.is_placeholder_key():
                active_providers.append(provider.name)
        
        if not active_providers:
            return {
                "available": False,
                "reason": "llm_providers_unavailable",
                "operator_action": "Configure a valid LLM API key in your environment variables (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY).",
                "error_details": "No active, non-placeholder LLM providers found."
            }
        return {"available": True, "active_providers": active_providers}
    except Exception as e:
        _log.error(f"Error checking LLM providers: {e}")
        return {
            "available": False,
            "reason": "llm_providers_unavailable",
            "operator_action": "Verify LLM configuration and environment variables.",
            "error_details": str(e)
        }

async def check_docker() -> Dict[str, Any]:
    """Checks if Docker is installed and responsive on the system."""
    try:
        # Run docker ps to see if daemon responds
        # Using a subprocess with a strict timeout to prevent hangs
        # Windows-compliant creation flags to hide window if needed
        import sys
        creationflags = 0
        if sys.platform == "win32":
            # subprocess.CREATE_NO_WINDOW
            creationflags = 0x08000000

        proc = await asyncio.create_subprocess_exec(
            "docker", "ps",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=creationflags
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=2.0)
            if proc.returncode == 0:
                return {"available": True}
            else:
                err_msg = stderr.decode().strip() or "Docker daemon is not running."
                return {
                    "available": False,
                    "reason": "docker_daemon_inactive",
                    "operator_action": "Start Docker Desktop or the Docker system service.",
                    "error_details": err_msg
                }
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except OSError:
                pass
            return {
                "available": False,
                "reason": "docker_daemon_inactive",
                "operator_action": "Verify Docker Desktop is running and responsive.",
                "error_details": "Docker command connection timed out."
            }
    except FileNotFoundError:
        return {
            "available": False,
            "reason": "docker_not_installed",
            "operator_action": "Install Docker Desktop for sandboxed agent operations.",
            "error_details": "Docker executable not found on path."
        }
    except Exception as e:
        return {
            "available": False,
            "reason": "docker_daemon_inactive",
            "operator_action": "Verify Docker daemon is active.",
            "error_details": str(e)
        }

def check_db() -> Dict[str, Any]:
    """Checks if veritabanı operates in degraded (SQLite fallback) or standard mode."""
    try:
        from libs.db.session import is_db_degraded, db_error
        degraded = is_db_degraded()
        if degraded:
            return {
                "available": True,
                "degraded": True,
                "reason": "database_degraded",
                "operator_action": "Verify primary PostgreSQL connection on port 5432 or 5433.",
                "error_details": db_error() or "Primary DB unreachable. SQLite fallback active."
            }
        return {"available": True, "degraded": False}
    except Exception as e:
        return {
            "available": False,
            "reason": "database_error",
            "operator_action": "Check database session imports and health.",
            "error_details": str(e)
        }

def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

async def check_runtime_dependencies(require_docker: bool | None = None) -> Dict[str, Any]:
    """
    Main entrypoint to check all dependencies.
    Aggregates checks and identifies the degraded state if any critical resource is missing.
    """
    docker_required = _env_flag("UI_REPAIR_REQUIRE_DOCKER", False) if require_docker is None else require_docker

    playwright_res = await check_playwright()
    llm_res = check_llm()
    docker_res = await check_docker()
    db_res = check_db()

    # Aggregate status
    if not playwright_res["available"]:
        return {
            "status": "degraded",
            "reason": playwright_res["reason"],
            "operator_action": playwright_res["operator_action"],
            "failed_stage": "evidence_collection",
            "error_details": playwright_res["error_details"],
            "fallback_used": "mock_evidence"
        }

    if not llm_res["available"]:
        return {
            "status": "degraded",
            "reason": llm_res["reason"],
            "operator_action": llm_res["operator_action"],
            "failed_stage": "autonomous_patch_generation",
            "error_details": llm_res["error_details"],
            "fallback_used": "mock_evidence"
        }

    if docker_required and not docker_res["available"]:
        return {
            "status": "degraded",
            "reason": docker_res["reason"],
            "operator_action": docker_res["operator_action"],
            "failed_stage": "sandboxed_execution",
            "error_details": docker_res["error_details"],
            "fallback_used": "local_mock_patch"
        }

    if db_res.get("degraded", False):
        return {
            "status": "degraded",
            "reason": db_res["reason"],
            "operator_action": db_res["operator_action"],
            "failed_stage": "persistence",
            "error_details": db_res["error_details"],
            "fallback_used": "sqlite_fallback"
        }

    warnings: List[Dict[str, Any]] = []
    if not docker_res["available"]:
        warnings.append({
            "stage": "sandboxed_execution",
            "reason": docker_res["reason"],
            "operator_action": docker_res["operator_action"],
            "fallback_used": "local_mock_patch",
            "error_details": docker_res["error_details"],
        })

    return {
        "status": "healthy",
        "warnings": warnings,
        "details": {
            "playwright": playwright_res,
            "llm": llm_res,
            "docker": {**docker_res, "required": docker_required},
            "db": db_res
        }
    }
