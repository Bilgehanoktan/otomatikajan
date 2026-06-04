from fastapi.testclient import TestClient

from services.integrations.free_web_api_catalog import (
    get_free_web_api_provider,
    list_free_web_api_providers,
)
from services.workflow_api.free_web_api_router import require_free_web_api_view
from services.workflow_api.main import app


def _test_identity():
    return {
        "id": "test-operator",
        "type": "operator",
        "role": "OPERATOR",
        "name": "Test Operator",
    }


def test_strict_catalog_contains_only_keyless_kotasiz_candidates():
    providers = list_free_web_api_providers(strict_kotasiz=True)
    provider_ids = {provider.id for provider in providers}

    assert {
        "ipify",
        "frankfurter",
        "exchange_api",
        "hexarate",
        "jsonplaceholder_dev",
        "freeapi_app",
        "countapi",
    }.issubset(provider_ids)
    assert "open_meteo" not in provider_ids
    assert "github_rest" not in provider_ids
    assert all(provider.auth_required is False for provider in providers)
    assert all(provider.strict_kotasiz is True for provider in providers)


def test_catalog_can_include_limited_free_candidates_when_requested():
    providers = list_free_web_api_providers(strict_kotasiz=False, include_limited=True)
    provider_ids = {provider.id for provider in providers}

    assert "open_meteo" in provider_ids
    assert "github_rest" in provider_ids
    assert get_free_web_api_provider("open_meteo").strict_kotasiz is False


def test_catalog_filters_by_category():
    providers = list_free_web_api_providers(category="currency")

    assert providers
    assert {provider.category for provider in providers} == {"currency"}


def test_free_web_api_catalog_endpoint_defaults_to_strict_mode():
    app.dependency_overrides[require_free_web_api_view] = _test_identity
    client = TestClient(app)

    try:
        response = client.get("/api/v1/free-web-apis/catalog")
    finally:
        app.dependency_overrides.pop(require_free_web_api_view, None)

    assert response.status_code == 200
    payload = response.json()
    provider_ids = {item["id"] for item in payload["items"]}

    assert payload["status"] == "success"
    assert payload["strict_kotasiz"] is True
    assert "exchange_api" in provider_ids
    assert "open_meteo" not in provider_ids
    assert payload["excluded_limited_count"] >= 1


def test_free_web_api_catalog_requires_authenticated_view_permission():
    app.dependency_overrides.pop(require_free_web_api_view, None)
    client = TestClient(app)

    response = client.get("/api/v1/free-web-apis/catalog")

    assert response.status_code == 401


def test_free_web_api_provider_detail_endpoint():
    app.dependency_overrides[require_free_web_api_view] = _test_identity
    client = TestClient(app)

    try:
        response = client.get("/api/v1/free-web-apis/providers/frankfurter")
    finally:
        app.dependency_overrides.pop(require_free_web_api_view, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"]["id"] == "frankfurter"
    assert payload["provider"]["auth_required"] is False


def test_free_web_api_openapi_schema_is_registered():
    schema = app.openapi()

    assert "/api/v1/free-web-apis/catalog" in schema["paths"]
    assert "/api/v1/free-web-apis/providers/{provider_id}" in schema["paths"]
