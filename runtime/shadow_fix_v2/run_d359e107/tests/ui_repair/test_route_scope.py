from libs.infra.router_registry import router_registry
from services.ui_repair.service import UIRepairService


def test_ui_repair_default_routes_match_live_nextjs_entrypoints():
    stale_routes = {"/dashboard", "/governance", "/learning", "/runtime-diagnostics"}

    assert stale_routes.isdisjoint(UIRepairService.DEFAULT_ROUTES)
    assert "/ops/launch-gates" in UIRepairService.DEFAULT_ROUTES
    assert "/ops/handover-status" in UIRepairService.DEFAULT_ROUTES
    assert "/governance/approvals" in UIRepairService.DEFAULT_ROUTES
    assert "/learning/strategy-memory" in UIRepairService.DEFAULT_ROUTES


def test_router_registry_uses_same_ui_repair_route_inventory():
    registry_routes = [route["path"] for route in router_registry.get_all_routes()]

    assert registry_routes == UIRepairService.DEFAULT_ROUTES
