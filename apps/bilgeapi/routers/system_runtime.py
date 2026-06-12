"""
apps/bilgeapi/routers/system_runtime.py — Phase 38
Exposes system runtime, release metadata, and autonomy mode configuration.
"""
import os
import sys
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request

from apps.bilgeapi.config import settings, AutonomyMode
from apps.bilgeapi.auth import require_permission

logger = logging.getLogger("bilgeapi.system_runtime")

router = APIRouter(prefix="/v1/system", tags=["System Runtime"])


@router.get("/release", response_model=Dict[str, Any])
async def get_release_metadata(
    request: Request,
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Returns release metadata, including active git commit hash, environment, tag, and versions.
    """
    git_sha = os.getenv("BILGEAPI_GIT_SHA", os.getenv("GIT_SHA", "unknown"))
    git_tag = os.getenv("BILGEAPI_GIT_TAG", os.getenv("GIT_TAG", "unknown"))
    
    # Simple dependency package extraction
    packages = {
        "fastapi": "0.115.8",
        "sqlalchemy": "2.0.38",
        "pydantic": "2.10.6",
    }
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        packages["fastapi"] = getattr(fastapi, "__version__", packages["fastapi"])
        packages["sqlalchemy"] = getattr(sqlalchemy, "__version__", packages["sqlalchemy"])
        packages["pydantic"] = getattr(pydantic, "__version__", packages["pydantic"])
    except ImportError:
        pass

    return {
        "service": "bilgeapi",
        "version": settings.BILGEAPI_VERSION,
        "environment": settings.APP_ENV,
        "git_commit": git_sha,
        "git_tag": git_tag,
        "python_version": sys.version.split()[0],
        "dependencies": packages
    }


@router.get("/autonomy", response_model=Dict[str, Any])
async def get_autonomy_mode_registry(
    request: Request,
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Returns the active autonomy mode, safe-allowed action scopes, and operator gates.
    """
    current_mode = settings.BILGEAPI_AUTONOMY_MODE
    
    # Safe Actions lists based on active mode
    safe_actions = []
    blocked_actions = []
    
    if current_mode in (AutonomyMode.SAFE_AUTONOMY, AutonomyMode.SUPERVISED_AUTONOMY, AutonomyMode.POLICY_BOUND_AUTONOMY):
        safe_actions = [
            "clear_local_cache",
            "stuck_job_cancel",
            "read-only_diagnostic",
            "sandbox_retry",
            "health_recheck",
            "evidence_regeneration"
        ]
        
    blocked_actions = [
        "container_restart",
        "db_migration",
        "production_config_change",
        "secret_rotation",
        "deploy_production",
        "rollback_production"
    ]

    return {
        "active_autonomy_mode": current_mode,
        "observe_only": current_mode == AutonomyMode.OBSERVE_ONLY,
        "safe_actions_enabled": len(safe_actions) > 0,
        "allowed_safe_actions": safe_actions,
        "human_gate_required_actions": blocked_actions,
        "auto_merge_policy": "auto_draft_pr_only"
    }
