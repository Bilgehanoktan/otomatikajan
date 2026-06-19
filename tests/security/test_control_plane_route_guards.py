import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from apps.public_api.main import app as public_app
from libs.db.session import get_db
from services.auth.jwt_auth import get_current_identity
from services.workflow_api.main import app as workflow_app


class _ScalarNoneResult:
    def scalar_one_or_none(self):
        return None


class _FakeDb:
    async def execute(self, *args, **kwargs):
        return _ScalarNoneResult()


async def _override_get_db():
    yield _FakeDb()


@pytest.fixture
async def workflow_client():
    workflow_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=workflow_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    workflow_app.dependency_overrides.clear()


@pytest.fixture
async def public_client():
    public_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=public_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    public_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_workflow_summary_requires_authentication(workflow_client):
    response = await workflow_client.get("/api/v1/workflows/stats/summary")

    assert response.status_code == 401


def test_public_api_registers_workflow_create_route():
    workflow_paths = {
        (route.path, tuple(sorted(route.methods or [])))
        for route in public_app.routes
        if "/api/v1/workflows" in getattr(route, "path", "")
    }

    assert any(
        path == "/api/v1/workflows" and "POST" in methods
        for path, methods in workflow_paths
    ), workflow_paths


@pytest.mark.asyncio
async def test_repair_lab_summary_requires_authentication(workflow_client):
    response = await workflow_client.get("/api/v1/repair-lab/summary")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ui_repair_overview_requires_authentication(public_client):
    response = await public_client.get("/api/v1/ui-repair/overview")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_observer_cannot_apply_repair_lab_patch(workflow_client, monkeypatch):
    monkeypatch.setenv("SIF_BASELINE_RBAC", "true")
    monkeypatch.delenv("SIF_DEV_AUTH_BYPASS", raising=False)

    async def _observer_identity():
        return {
            "id": uuid.uuid4(),
            "type": "operator",
            "role": "AUDIT_OBSERVER",
            "email": "observer@test.local",
            "name": "Read Only Observer",
        }

    workflow_app.dependency_overrides[get_current_identity] = _observer_identity

    response = await workflow_client.post("/api/v1/repair-lab/cases/case-123/apply-patch")

    assert response.status_code == 403
    assert "ACCESS DENIED" in response.json()["detail"]
