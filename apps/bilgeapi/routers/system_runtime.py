"""
apps/bilgeapi/routers/system_runtime.py — Phase 38
Exposes system runtime, release metadata, and autonomy mode configuration.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, HTTPException

from apps.bilgeapi.config import settings, AutonomyMode
from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.schemas.autonomy import (
    AutonomyDecisionRequest,
    AutonomyDecisionResponse,
    ManagementGateResponse,
    ManagementGateUpdateRequest,
)
from apps.bilgeapi.routers.deps import get_autonomy_decision_service
from apps.bilgeapi.services.i18n import get_locale, i18n_service
from apps.bilgeapi.services.self_healing import SelfHealingPolicy

logger = logging.getLogger("bilgeapi.system_runtime")

router = APIRouter(prefix="/v1/system", tags=["System Runtime"])


def _management_gate_payload(
    identity: Optional[dict] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    unlocked = settings.BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED
    return {
        "unlocked": unlocked,
        "status": "UNLOCKED" if unlocked else "LOCKED",
        "reason": reason,
        "forbidden_actions": SelfHealingPolicy.FORBIDDEN_ACTIONS,
        "human_gate_required": settings.BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED,
        "updated_by": identity.get("id") if identity else None,
    }


def get_git_metadata() -> Dict[str, str]:
    """
    Resolves the active Git commit SHA and tag.
    1. Reads environment variables (which are populated from .env).
    2. Runs git CLI if .git exists.
    3. Reads local fallback files .git_commit and .git_tag.
    """
    git_sha = os.getenv("BILGEAPI_GIT_SHA") or os.getenv("GIT_SHA")
    git_tag = os.getenv("BILGEAPI_GIT_TAG") or os.getenv("GIT_TAG")
    
    if not git_sha or not git_tag or git_sha == "unknown" or git_tag == "unknown":
        try:
            import subprocess
            current_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = current_dir
            for _ in range(5):
                if os.path.exists(os.path.join(repo_root, ".git")):
                    break
                repo_root = os.path.dirname(repo_root)
            
            if not git_sha or git_sha == "unknown":
                res_sha = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=repo_root,
                    check=True
                )
                git_sha = res_sha.stdout.strip()
                
            if not git_tag or git_tag == "unknown":
                res_tag = subprocess.run(
                    ["git", "describe", "--tags", "--always", "--dirty"],
                    capture_output=True,
                    text=True,
                    cwd=repo_root,
                    check=True
                )
                git_tag = res_tag.stdout.strip()
        except Exception:
            pass

    current_dir = os.path.dirname(os.path.abspath(__file__))
    commit_file = os.path.join(current_dir, ".git_commit")
    tag_file = os.path.join(current_dir, ".git_tag")
    
    if (not git_sha or git_sha == "unknown") and os.path.exists(commit_file):
        try:
            with open(commit_file, "r", encoding="utf-8") as f:
                git_sha = f.read().strip()
        except Exception:
            pass
            
    if (not git_tag or git_tag == "unknown") and os.path.exists(tag_file):
        try:
            with open(tag_file, "r", encoding="utf-8") as f:
                git_tag = f.read().strip()
        except Exception:
            pass

    return {
        "git_commit": git_sha or "unknown",
        "git_tag": git_tag or "unknown"
    }


@router.get("/release", response_model=Dict[str, Any])
async def get_release_metadata(
    request: Request,
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Returns release metadata, including active git commit hash, environment, tag, and versions.
    """
    git_meta = get_git_metadata()
    git_sha = git_meta["git_commit"]
    git_tag = git_meta["git_tag"]
    
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
            "health_recheck",
            "read-only_diagnostic",
            "stuck_job_cancel",
            "sandbox_retry",
            "evidence_regeneration",
            "generate_evidence",
            "refresh_registry_cache",
            "collect_logs"
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


@router.get("/queue/status", response_model=Dict[str, Any])
async def get_queue_status(
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Returns the current status of the AgentOrchestrationQueue.
    """
    from libs.db.session import session_scope
    from apps.bilgeapi.models.database import AgentTaskQueueModel, AgentTaskLeaseModel, AgentOrchestrationRunModel
    from sqlalchemy import select, func

    async with session_scope() as db:
        # Task counts by status
        status_stmt = select(AgentTaskQueueModel.status, func.count(AgentTaskQueueModel.task_id)).group_by(AgentTaskQueueModel.status)
        status_res = await db.execute(status_stmt)
        status_counts = {status: count for status, count in status_res.all()}

        # Total tasks
        total_stmt = select(func.count(AgentTaskQueueModel.task_id))
        total_res = await db.execute(total_stmt)
        total_tasks = total_res.scalar() or 0

        # Active leases
        lease_stmt = select(func.count(AgentTaskLeaseModel.task_id))
        lease_res = await db.execute(lease_stmt)
        active_leases = lease_res.scalar() or 0

        # Recent runs count
        runs_stmt = select(AgentOrchestrationRunModel.status, func.count(AgentOrchestrationRunModel.task_id)).group_by(AgentOrchestrationRunModel.status)
        runs_res = await db.execute(runs_stmt)
        runs_counts = {status: count for status, count in runs_res.all()}

        return {
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "active_leases": active_leases,
            "orchestration_runs": runs_counts
        }


@router.get("/management-gate", response_model=ManagementGateResponse)
async def get_management_gate(
    request: Request,
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Returns the operator-controlled gate for management actions.
    """
    return _management_gate_payload(identity=identity)


@router.post("/management-gate", response_model=ManagementGateResponse)
async def update_management_gate(
    request: ManagementGateUpdateRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Locks or unlocks management actions. Forbidden actions remain blocked by policy.
    """
    settings.BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED = request.unlocked
    return _management_gate_payload(identity=identity, reason=request.reason)


@router.post("/autonomy/decide", response_model=AutonomyDecisionResponse)
async def evaluate_autonomy_eligibility(
    request: AutonomyDecisionRequest,
    decision_engine: Any = Depends(get_autonomy_decision_service),
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Evaluates incident classification, risk score, otonomi eligibility limits
    and maps required human gates. Logs the decision to the DB.
    """
    try:
        decision = await decision_engine.decide(request.incident_id, request.action_type)
        return decision
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing autonomy decision: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error executing autonomy decision")


@router.get("/i18n/test", response_model=Dict[str, Any])
async def test_localization(
    request: Request,
    lang: str = Depends(get_locale)
):
    """
    Returns localized responses for testing the language pack.
    """
    return {
        "lang": lang,
        "welcome_message": i18n_service.translate("welcome_message", lang),
        "status_healthy": i18n_service.translate("status_healthy", lang),
        "auth_required": i18n_service.translate("auth_required", lang),
        "forbidden": i18n_service.translate("forbidden", lang),
        "not_found": i18n_service.translate("not_found", lang)
    }


@router.get("/profile", response_model=Dict[str, Any])
async def get_system_profile(
    request: Request,
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Builds and returns the workspace system profile and health score.
    """
    from apps.bilgeapi.core.workspace import WorkspaceManager
    from apps.bilgeapi.core.system_profile import SystemProfiler
    from apps.bilgeapi.core.health_score import HealthScorer

    manager = WorkspaceManager()
    profiler = SystemProfiler(manager.project_root, manager.workspace_dir)
    profile = profiler.build_profile()

    scorer = HealthScorer(manager.project_root, manager.workspace_dir)
    health = scorer.calculate_score(profile)

    return {
        "profile": profile,
        "health": health
    }


