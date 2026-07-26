from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.social_growth.content_orchestrator import (
    ContentOrchestrator,
)
from services.social_growth.creative_planner import (
    CreativeDraft,
    CreativeProductionAgent,
    OpenAICreativePlanner,
)
from services.social_growth.creative_router import build_creative_agent_router

TEST_API_KEY = "creative-api-key-value-at-least-32-characters"


class FakeResponses:
    def parse(self, **kwargs: Any) -> object:
        del kwargs
        draft = CreativeDraft(
            hook="Tek promptla sonucu göster.",
            script_beats=["Sonuç", "Prompt", "Sınırlama"],
            caption="Kaynaklı kısa demo.",
            video_prompt="Portrait 9:16 concise product demo.",
            cta="Kaydet ve paylaş.",
            source_urls=[],
            safety_notes=["İnsan onayı zorunlu."],
        )
        return type("Parsed", (), {"output_parsed": draft})()


class FakeOpenAIClient:
    responses = FakeResponses()


def payload() -> dict[str, Any]:
    return {
        "topic": "AI video demo",
        "audience": "freelancerlar",
        "mode": "reach",
        "format": "reel",
        "template": "one_prompt_demo",
        "cta_mode": "save_share",
    }


def test_creative_router_is_authenticated_and_returns_approval_waiting_package() -> None:
    agent = CreativeProductionAgent(
        ContentOrchestrator(),
        OpenAICreativePlanner(FakeOpenAIClient()),
    )
    app = FastAPI()
    app.include_router(build_creative_agent_router(agent, api_key=TEST_API_KEY))
    client = TestClient(app)

    unauthorized = client.post("/content/creative-packages", json=payload())
    response = client.post(
        "/content/creative-packages",
        json=payload(),
        headers={"X-Content-Orchestrator-Key": TEST_API_KEY},
    )

    assert unauthorized.status_code == 401
    assert response.status_code == 201
    assert response.json()["status"] == "AWAITING_HUMAN_APPROVAL"
    assert response.json()["external_actions_performed"] is False


def test_creative_router_returns_service_unavailable_when_openai_is_not_configured() -> None:
    app = FastAPI()
    app.include_router(build_creative_agent_router(None, api_key=TEST_API_KEY))
    response = TestClient(app).post(
        "/content/creative-packages",
        json=payload(),
        headers={"X-Content-Orchestrator-Key": TEST_API_KEY},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "CREATIVE_PLANNER_NOT_CONFIGURED"
