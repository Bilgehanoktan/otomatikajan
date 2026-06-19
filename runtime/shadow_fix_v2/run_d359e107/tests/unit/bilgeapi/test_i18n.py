import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.bilgeapi.services.i18n import I18nService, get_locale, i18n_service
from apps.bilgeapi.routers.system_runtime import router

def test_i18n_service_translations():
    # Test English translations
    assert i18n_service.translate("welcome_message", "en") == "Welcome to BilgeAPI Sovereign Control Plane"
    assert i18n_service.translate("welcome_message", "en-US") == "Welcome to BilgeAPI Sovereign Control Plane"
    
    # Test Turkish translations
    assert i18n_service.translate("welcome_message", "tr") == "Sovereign Control Plane BilgeAPI'ye Hoş Geldiniz"
    assert i18n_service.translate("welcome_message", "tr-TR") == "Sovereign Control Plane BilgeAPI'ye Hoş Geldiniz"
    
    # Test missing keys fallback to key itself
    assert i18n_service.translate("non_existent_key", "en") == "non_existent_key"
    assert i18n_service.translate("non_existent_key", "tr") == "non_existent_key"

def test_fastapi_i18n_endpoint():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    # 1. Default (no headers, no query params) -> en
    response = client.get("/v1/system/i18n/test")
    assert response.status_code == 200
    data = response.json()
    assert data["lang"] == "en"
    assert data["welcome_message"] == "Welcome to BilgeAPI Sovereign Control Plane"

    # 2. Query param lang=tr -> tr
    response = client.get("/v1/system/i18n/test?lang=tr")
    assert response.status_code == 200
    data = response.json()
    assert data["lang"] == "tr"
    assert data["welcome_message"] == "Sovereign Control Plane BilgeAPI'ye Hoş Geldiniz"

    # 3. Accept-Language header -> tr
    response = client.get("/v1/system/i18n/test", headers={"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"})
    assert response.status_code == 200
    data = response.json()
    assert data["lang"] == "tr"
    assert data["welcome_message"] == "Sovereign Control Plane BilgeAPI'ye Hoş Geldiniz"

    # 4. Accept-Language header -> en
    response = client.get("/v1/system/i18n/test", headers={"Accept-Language": "en-US,en;q=0.9"})
    assert response.status_code == 200
    data = response.json()
    assert data["lang"] == "en"
    assert data["welcome_message"] == "Welcome to BilgeAPI Sovereign Control Plane"
