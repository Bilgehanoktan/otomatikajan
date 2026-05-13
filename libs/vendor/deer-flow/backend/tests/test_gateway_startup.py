"""Gateway startup regression tests."""


def test_gateway_app_imports_and_registers_core_routes() -> None:
    """Gateway import should not require legacy orchestration package aliases."""
    from app.gateway.app import create_app

    app = create_app()
    route_paths = {route.path for route in app.routes}

    assert "/health" in route_paths
    assert "/api/memory" in route_paths
    assert "/api/skills" in route_paths
    assert "/api/agents" in route_paths
