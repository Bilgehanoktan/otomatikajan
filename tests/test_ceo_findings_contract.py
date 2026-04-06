from __future__ import annotations
from fastapi.testclient import TestClient
import pytest

def test_ceo_findings_endpoint_discloses_fallback_source(monkeypatch) -> None:
    from api.ceo_router import router
    from fastapi import FastAPI
    import sys
    import types

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def _fake_user():
        return {"email": "audit@example.com", "is_admin": True}

    # Mock dependencies - Auth and Repair ingestion
    from apps.api.routers.auth import jwt_auth
    app.dependency_overrides[jwt_auth.get_current_user] = _fake_user

    class FakeIngestor:
        def list_open(self):
            return []

    # Injecting module mock to avoid real dependencies if needed
    mod = types.ModuleType("packages.repair_engine.ingestion.incident_ingestor")
    mod.incident_ingestor = FakeIngestor()
    sys.modules["packages.repair_engine.ingestion.incident_ingestor"] = mod

    client = TestClient(app)
    res = client.get("/api/v1/ceo/findings")
    assert res.status_code == 200
    body = res.json()
    assert "is_fallback" in body
    assert "source_of_truth" in body
    # Since we are mocking a fake environment or if DB is empty in test
    assert body["source_of_truth"] in ["sovereign_db", "sovereign_db_empty"]
