def test_auth_router_module_exists():
    from apps.api.routers.apps.api.routers.auth.router import router
    assert router is not None
