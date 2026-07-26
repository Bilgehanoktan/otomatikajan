from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.social_growth.audit import EpisodeEvidenceSink
from services.social_growth.content_orchestrator import (
    Claim,
    ContentBrief,
    ContentFormat,
    ContentMode,
    ContentOrchestrator,
    ContentTemplate,
    CTAMode,
    DuplicateKeywordError,
    ProviderRoutingMode,
    RedisKeywordRegistry,
    UngroundedClaimError,
    VideoProvider,
)
from services.social_growth.content_router import build_content_orchestrator_router

TEST_PLANNER_API_KEY = "planner-api-key-value-at-least-32-characters"


def make_brief(**overrides: object) -> ContentBrief:
    values: dict[str, object] = {
        "topic": "yapay zekâ ile kısa video üretimi",
        "audience": "freelancer ve küçük işletmeler",
        "mode": ContentMode.SAVE,
        "format": ContentFormat.CAROUSEL,
        "template": ContentTemplate.TOOL_CAROUSEL,
        "cta_mode": CTAMode.SAVE_SHARE,
    }
    values.update(overrides)
    return ContentBrief(**values)  # type: ignore[arg-type]


def test_tool_carousel_plan_is_saveable_and_has_no_video_provider() -> None:
    plan = ContentOrchestrator().plan(make_brief())

    assert plan.status == "DRY_RUN"
    assert plan.template is ContentTemplate.TOOL_CAROUSEL
    assert len(plan.hooks) == 3
    assert [unit.kind for unit in plan.content_units] == [
        "cover",
        "tool_list",
        "selection_guide",
        "cta",
    ]
    assert plan.provider_route.stages == ()
    assert plan.cta.keyword is None
    assert "saves" in plan.metrics
    assert "human_approval" in plan.quality_gates


@pytest.mark.parametrize(
    ("routing_mode", "expected_providers", "expected_roles"),
    [
        (ProviderRoutingMode.AUTO, (VideoProvider.SEEDANCE,), ("generate",)),
        (
            ProviderRoutingMode.COMPARE,
            (VideoProvider.SEEDANCE, VideoProvider.KLING),
            ("candidate", "candidate"),
        ),
        (
            ProviderRoutingMode.PIPELINE,
            (VideoProvider.SEEDANCE, VideoProvider.KLING),
            ("generate", "refine"),
        ),
    ],
)
def test_demo_reel_routes_video_providers_deterministically(
    routing_mode: ProviderRoutingMode,
    expected_providers: tuple[VideoProvider, ...],
    expected_roles: tuple[str, ...],
) -> None:
    plan = ContentOrchestrator().plan(
        make_brief(
            mode=ContentMode.LEAD,
            format=ContentFormat.REEL,
            template=ContentTemplate.ONE_PROMPT_DEMO,
            cta_mode=CTAMode.KEYWORD_DM,
            keyword="PROMPT",
            routing_mode=routing_mode,
        )
    )

    assert tuple(stage.provider for stage in plan.provider_route.stages) == expected_providers
    assert tuple(stage.role for stage in plan.provider_route.stages) == expected_roles
    assert plan.cta.keyword == "PROMPT"
    assert plan.cta.fulfilment == "configured_dm_asset"


def test_emotional_story_auto_route_prefers_cinematic_profile() -> None:
    plan = ContentOrchestrator().plan(
        make_brief(
            mode=ContentMode.REACH,
            format=ContentFormat.REEL,
            template=ContentTemplate.EMOTIONAL_MINI_STORY,
        )
    )

    assert plan.provider_route.stages[0].provider is VideoProvider.VEO
    assert plan.hooks[0].category == "emotional"
    assert "three_second_hold_rate" in plan.metrics
    assert "completion_rate" in plan.metrics


def test_keyword_dm_requires_a_safe_unique_keyword() -> None:
    orchestrator = ContentOrchestrator()
    brief = make_brief(
        mode=ContentMode.LEAD,
        format=ContentFormat.REEL,
        template=ContentTemplate.ONE_PROMPT_DEMO,
        cta_mode=CTAMode.KEYWORD_DM,
        keyword="PROMPT",
    )

    orchestrator.plan(brief)

    with pytest.raises(DuplicateKeywordError, match="PROMPT"):
        orchestrator.plan(brief)

    with pytest.raises(ValueError, match="keyword"):
        make_brief(cta_mode=CTAMode.KEYWORD_DM, keyword="iki kelime")


class FakeKeywordRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set(self, name: str, value: str, *, nx: bool, ex: int) -> bool:
        del ex
        if nx and name in self.values:
            return False
        self.values[name] = value
        return True

    def eval(self, script: str, numkeys: int, *keys_and_args: str) -> int:
        del script, numkeys
        key, expected_owner = keys_and_args
        if self.values.get(key) != expected_owner:
            return 0
        del self.values[key]
        return 1


def test_redis_keyword_registry_is_shared_and_owner_safe() -> None:
    redis = FakeKeywordRedis()
    first = RedisKeywordRegistry(redis)
    second = RedisKeywordRegistry(redis)

    assert first.claim("PROMPT", "plan-1") is True
    assert second.claim("PROMPT", "plan-2") is False

    second.release("PROMPT", "plan-2")
    assert second.claim("PROMPT", "plan-2") is False

    first.release("PROMPT", "plan-1")
    assert second.claim("PROMPT", "plan-2") is True


def test_verifiable_claim_without_https_source_is_blocked() -> None:
    with pytest.raises(UngroundedClaimError, match="kaynak"):
        ContentOrchestrator().plan(
            make_brief(
                claims=(
                    Claim(
                        text="Bu araç sınırsız ve ücretsiz video üretir.",
                        verifiable=True,
                    ),
                )
            )
        )

    plan = ContentOrchestrator().plan(
        make_brief(
            claims=(
                Claim(
                    text="Sağlayıcının duyurduğu özellik kullanıma açıldı.",
                    source_urls=("https://provider.example.com/release",),
                ),
            )
        )
    )
    assert plan.claims[0].source_urls == ("https://provider.example.com/release",)


def test_plan_records_dry_run_episode_evidence(tmp_path: Path) -> None:
    evidence_path = tmp_path / "content_plan_evidence.jsonl"
    plan = ContentOrchestrator(
        evidence_sink=EpisodeEvidenceSink(evidence_path)
    ).plan(make_brief())
    episode = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert episode["actions"][0]["step_id"] == "content_campaign_plan"
    assert episode["actions"][0]["success"] is False
    assert episode["actions"][0]["input_data"]["metadata"]["plan_id"] == plan.plan_id
    assert episode["verification"]["safe_to_finalize"] is True
    assert episode["verification"]["safe_to_learn"] is False


def test_content_plan_api_returns_a_side_effect_free_contract() -> None:
    app = FastAPI()
    app.include_router(
        build_content_orchestrator_router(
            ContentOrchestrator(),
            api_key=TEST_PLANNER_API_KEY,
        ),
        prefix="/api/v1/social-growth",
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/social-growth/content/plans",
        json={
            "topic": "tek promptla ürün videosu",
            "audience": "e-ticaret işletmeleri",
            "mode": "lead",
            "format": "reel",
            "template": "one_prompt_demo",
            "cta_mode": "keyword_dm",
            "keyword": "VİDEO",
            "routing_mode": "compare",
            "claims": [
                {
                    "text": "Bu demo sağlayıcının belgelenmiş özelliğini kullanır.",
                    "source_urls": ["https://provider.example.com/docs"],
                }
            ],
        },
        headers={"X-Content-Orchestrator-Key": TEST_PLANNER_API_KEY},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "DRY_RUN"
    assert payload["external_actions_performed"] is False
    assert [stage["provider"] for stage in payload["provider_route"]["stages"]] == [
        "seedance",
        "kling",
    ]
    assert payload["cta"]["keyword"] == "VİDEO"


def test_content_plan_api_fails_closed_for_ungrounded_claim() -> None:
    app = FastAPI()
    app.include_router(
        build_content_orchestrator_router(
            ContentOrchestrator(),
            api_key=TEST_PLANNER_API_KEY,
        )
    )
    client = TestClient(app)

    response = client.post(
        "/content/plans",
        json={
            "topic": "ücretsiz AI videosu",
            "audience": "içerik üreticileri",
            "mode": "reach",
            "format": "reel",
            "template": "one_prompt_demo",
            "cta_mode": "save_share",
            "claims": [{"text": "Tamamen ücretsiz ve sınırsızdır."}],
        },
        headers={"X-Content-Orchestrator-Key": TEST_PLANNER_API_KEY},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "BLOCKED_UNGROUNDED_CLAIM"


class DenyAllLimiter:
    def allow(self, client_key: str) -> bool:
        del client_key
        return False


def test_content_plan_api_requires_operator_key_and_rate_limits() -> None:
    app = FastAPI()
    app.include_router(
        build_content_orchestrator_router(
            ContentOrchestrator(),
            api_key=TEST_PLANNER_API_KEY,
            rate_limiter=DenyAllLimiter(),
        )
    )
    client = TestClient(app)
    payload = {
        "topic": "AI araçları",
        "audience": "küçük işletmeler",
        "mode": "save",
        "format": "carousel",
        "template": "tool_carousel",
        "cta_mode": "save_share",
    }

    missing = client.post("/content/plans", json=payload)
    invalid = client.post(
        "/content/plans",
        json=payload,
        headers={"X-Content-Orchestrator-Key": "wrong-key"},
    )
    limited = client.post(
        "/content/plans",
        json=payload,
        headers={"X-Content-Orchestrator-Key": TEST_PLANNER_API_KEY},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert limited.status_code == 429


def test_content_plan_router_rejects_weak_operator_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        build_content_orchestrator_router(ContentOrchestrator(), api_key="short")
