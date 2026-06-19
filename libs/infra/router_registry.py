"""
libs/infra/router_registry.py — Phase 13.04
Centralized router registration for Sovereign AGI services.
"""
from fastapi import FastAPI

def register_routers(app: FastAPI):
    """
    Registers all service routers to the main FastAPI application.
    All API endpoints are prefixed with /api/v1 to avoid conflicts with
    static dashboard files served at the root.
    """
    from fastapi import APIRouter
    
    print("[DEBUG] Router Registry: Loading routers...")
    # Lazy load routers inside the function to prevent circular imports and startup hangs
    print("[DEBUG] Loading workflow_router...")
    from services.workflow_api.router import router as workflow_router
    print("[DEBUG] Loading auth_router...")
    from services.auth.router import router as auth_router
    print("[DEBUG] Loading metrics_router...")
    from services.workflow_api.metrics_router import router as metrics_router
    print("[DEBUG] Loading health_router...")
    from services.workflow_api.health_router import router as health_router
    print("[DEBUG] Loading compatibility_router...")
    from services.workflow_api.compatibility_router import router as compatibility_router
    print("[DEBUG] Loading mesh_router...")
    from services.observability.mesh_status_api import router as mesh_router
    print("[DEBUG] Loading fleet_router...")
    from services.observability.fleet_status_api import router as fleet_router
    print("[DEBUG] Loading mesh_actions_router...")
    from services.governance.mesh_actions_api import router as mesh_actions_router
    print("[DEBUG] Loading repair_lab_router...")
    from services.workflow_api.repair_lab_router import router as repair_lab_router
    print("[DEBUG] Loading fleet_orchestra_router...")
    from services.workflow_api.fleet_router import router as fleet_orchestra_router
    print("[DEBUG] Loading ceo_router...")
    from services.orchestration.ceo.router import router as ceo_engine_router
    from services.workflow_api.ceo_router import router as ceo_bridge_router
    from services.ui_repair.router import router as ui_repair_router
    from services.workflow_api.project_factory_router import router as project_factory_router
    from services.workflow_api.free_web_api_router import router as free_web_api_router
    from services.repair.external_agents.router import router as agents_router
    
    api_v1 = APIRouter(prefix="/api/v1")

    # 1. Auth Service (mapped to /api/v1/auth)
    api_v1.include_router(auth_router, prefix="/auth", tags=["Auth"])

    # 2. Workflow API
    api_v1.include_router(workflow_router)

    # 3. Phase 17 Metrics API (Now mapped to /api/v1/metrics/phase17)
    api_v1.include_router(metrics_router)

    # 4. Governance & Self-Healing
    print("[DEBUG] Loading governance_router...")
    from services.workflow_api.governance_router import router as governance_router
    api_v1.include_router(governance_router, prefix="/governance")

    # 5. Health & compatibility endpoints used during migration
    api_v1.include_router(health_router, prefix="/health")
    api_v1.include_router(compatibility_router)

    # 6. Observability & Fleet Status
    api_v1.include_router(mesh_router, prefix="/mesh")
    api_v1.include_router(mesh_actions_router, prefix="/mesh/actions")
    api_v1.include_router(fleet_router, prefix="/fleet")
    api_v1.include_router(fleet_orchestra_router, prefix="/fleet/ops")

    # 7. Repair Lab & Self-Tuning
    api_v1.include_router(repair_lab_router, prefix="/repair-lab")

    @api_v1.get("/improvements", tags=["Compatibility"])
    async def list_improvements_alias(limit: int = 20):
        from services.workflow_api.repair_lab_router import list_improvements

        return await list_improvements(limit=limit)

    # 8. Phase 31: Autonomous Learning & Governance Harness
    print("[DEBUG] Loading learning_router...")
    from services.governance.learning_api import router as learning_router
    print("[DEBUG] Loading governor_router...")
    from services.workflow_api.governor_router import router as governor_router
    print("[DEBUG] Loading harness_router...")
    from services.governance.harness_api import router as harness_router
    print("[DEBUG] Loading mcp_router...")
    from services.workflow_api.mcp_router import router as mcp_router
    print("[DEBUG] Loading debate_router...")
    from services.workflow_api.debate_router import router as debate_router
    
    api_v1.include_router(learning_router)
    api_v1.include_router(governor_router, prefix="/governance/governor")
    api_v1.include_router(governor_router, prefix="/governance/inbox/governor", tags=["Compatibility"])
    api_v1.include_router(debate_router, prefix="/debate")
    api_v1.include_router(ceo_engine_router, prefix="/ceo")
    api_v1.include_router(ceo_bridge_router, prefix="/ceo")
    api_v1.include_router(harness_router, prefix="/harness", tags=["Harness API"])
    api_v1.include_router(mcp_router, prefix="/mcp")
    api_v1.include_router(ui_repair_router, prefix="/ui-repair")
    api_v1.include_router(project_factory_router, prefix="/project-factory")
    api_v1.include_router(free_web_api_router, prefix="/free-web-apis")
    api_v1.include_router(agents_router, prefix="/agents")
    
    # 8.1 Aliases for Refine Compatibility
    api_v1.include_router(governance_router, prefix="/axiology", tags=["Compatibility"]) # Alias for /axiology
    api_v1.include_router(mcp_router, prefix="/mcp-hub", tags=["Compatibility"]) # Alias for /mcp-hub

    # Register the unified API router
    app.include_router(api_v1)
    print("[DEBUG] All routers registered successfully.")


class RouterRegistry:
    """
    Registry for UI and API routes.
    """
    @staticmethod
    def get_all_routes():
        # Returns the UI routes to be monitored
        return [
            {"path": "/"},
            {"path": "/project-factory"},
            {"path": "/workflows"},
            {"path": "/repair-lab"},
            {"path": "/system-health"},
            {"path": "/ops/handover-status"},
            {"path": "/ops/launch-gates"},
            {"path": "/governance/approvals"},
            {"path": "/governance/safety"},
            {"path": "/audit"},
            {"path": "/approvals"},
            {"path": "/incidents"},
            {"path": "/costs"},
            {"path": "/learning/strategy-memory"},
            {"path": "/compliance"},
            {"path": "/fleet"},
            {"path": "/mesh"},
            {"path": "/federation"},
            {"path": "/evolution"}
        ]

router_registry = RouterRegistry()
