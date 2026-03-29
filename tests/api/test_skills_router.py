from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.skills_router import router
from auth.jwt_auth import get_current_user

def mock_get_current_user():
    return {"id": "test-user", "role": "admin"}

def build_test_app():
    app = FastAPI()
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.include_router(router, prefix="/api/v1")
    return app


def test_skills_router_lists_skills():
    client = TestClient(build_test_app())

    response = client.get("/api/v1/skills")

    assert response.status_code == 200
    body = response.json()
    assert "skills" in body
    assert "optimization" in body["skills"]
    assert "debugging" in body["skills"]
    assert "file_search" in body["skills"]
    assert "vault_memory" in body["skills"]
    assert "skill_creator" in body["skills"]


def test_skills_router_suggest_bug_text():
    client = TestClient(build_test_app())

    response = client.post(
        "/api/v1/skills/suggest",
        json={
            "task_type": "generic",
            "title": "repair_router await bug",
            "description": "There is an async bug and traceback in repair router.",
        },
    )

    assert response.status_code == 200
    suggested = response.json()["suggestions"]
    assert "debugging" in suggested
    assert "file_search" in suggested
    assert "vault_memory" in suggested


def test_skills_router_suggest_reusable_workflow():
    client = TestClient(build_test_app())

    response = client.post(
        "/api/v1/skills/suggest",
        json={
            "task_type": "generic",
            "title": "create reusable workflow",
            "description": "Repeated recovery flow should be turned into a reusable skill template",
        },
    )

    assert response.status_code == 200
    suggested = response.json()["suggestions"]
    assert "skill_creator" in suggested


def test_skills_router_rejects_invalid_body():
    client = TestClient(build_test_app())

    response = client.post(
        "/api/v1/skills/suggest",
        json={"description": "missing title"},
    )

    assert response.status_code == 422
