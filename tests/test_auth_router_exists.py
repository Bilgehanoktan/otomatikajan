def test_auth_router_module_exists():
    from auth.router import router
    assert router is not None
