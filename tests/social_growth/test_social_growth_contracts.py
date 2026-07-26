from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.social_growth.app import create_app
from services.social_growth.audit import EpisodeEvidenceSink
from services.social_growth.config import ConfigurationError, MetaSettings
from services.social_growth.contracts import EvidenceError, OperationEvidence, OperationStatus
from services.social_growth.meta_client import GraphAPIError, GraphResponse, MetaGraphClient
from services.social_growth.rate_limit import RedisWebhookRateLimiter
from services.social_growth.router import build_meta_webhook_router
from services.social_growth.service import (
    CommentEvent,
    InMemoryIdempotencyStore,
    RedisIdempotencyStore,
    SocialGrowthService,
)
from services.social_growth.webhook import SignatureError, parse_comment_events, verify_signature

TEST_ACCESS_TOKEN = "access-token-secret-long-enough"
TEST_APP_SECRET = "app-secret-value-with-at-least-32-bytes"


class FakeTransport:
    def __init__(self, responses: list[GraphResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> GraphResponse:
        self.requests.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "data": data,
                "headers": headers,
            }
        )
        return self.responses.pop(0)


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set(self, name: str, value: str, *, nx: bool, ex: int) -> bool:
        del ex
        if nx and name in self.values:
            return False
        self.values[name] = value
        return True

    def delete(self, *names: str) -> int:
        removed = 0
        for name in names:
            if name in self.values:
                del self.values[name]
                removed += 1
        return removed

    def incr(self, name: str) -> int:
        value = int(self.values.get(name, "0")) + 1
        self.values[name] = str(value)
        return value

    def expire(self, name: str, ttl_seconds: int) -> bool:
        del ttl_seconds
        return name in self.values


def make_settings() -> MetaSettings:
    return MetaSettings(
        account_id="17841400000000000",
        access_token=TEST_ACCESS_TOKEN,
        app_secret=TEST_APP_SECRET,
        verify_token="verify-token-value",
        api_version="v23.0",
    )


def test_settings_fail_closed_and_redact_secrets() -> None:
    with pytest.raises(ConfigurationError, match="INSTAGRAM_ACCOUNT_ID"):
        MetaSettings.from_env({})

    settings = make_settings()
    rendered = repr(settings)

    assert TEST_ACCESS_TOKEN not in rendered
    assert TEST_APP_SECRET not in rendered
    assert "verify-token-value" not in rendered
    assert "***REDACTED***" in rendered

    with pytest.raises(ConfigurationError, match="META_APP_SECRET"):
        MetaSettings(
            account_id="17841400000000000",
            access_token=TEST_ACCESS_TOKEN,
            app_secret="too-short",
            verify_token="verify-token-value",
            api_version="v23.0",
        )


def test_success_evidence_requires_real_provider_id() -> None:
    with pytest.raises(EvidenceError, match="provider_id"):
        OperationEvidence(
            operation="carousel_publish",
            status=OperationStatus.SUCCEEDED,
        )

    dry_run = OperationEvidence(
        operation="carousel_publish",
        status=OperationStatus.DRY_RUN,
    )
    assert dry_run.status is OperationStatus.DRY_RUN


def test_webhook_hmac_is_verified_before_payload_is_parsed() -> None:
    body = json.dumps(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "field": "comments",
                            "value": {
                                "id": "comment-123",
                                "text": "PROMPT rehberini gönder",
                                "from": {"username": "example_user"},
                            },
                        }
                    ]
                }
            ]
        },
        separators=(",", ":"),
    ).encode()
    signature = "sha256=" + hmac.new(
        TEST_APP_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    verify_signature(body, signature, TEST_APP_SECRET)
    events = parse_comment_events(body)

    assert events == [
        CommentEvent(
            comment_id="comment-123",
            text="PROMPT rehberini gönder",
            username="example_user",
        )
    ]

    with pytest.raises(SignatureError):
        verify_signature(body, "sha256=bad", TEST_APP_SECRET)


@pytest.mark.parametrize("count", [0, 1, 11])
def test_carousel_rejects_invalid_media_count_without_network(count: int) -> None:
    transport = FakeTransport([])
    service = SocialGrowthService(
        MetaGraphClient(make_settings(), transport),
        InMemoryIdempotencyStore(),
    )

    with pytest.raises(ValueError, match="2 ile 10"):
        service.publish_carousel(
            [f"https://cdn.example.com/slide-{index}.png" for index in range(count)],
            "Açıklama",
        )

    assert transport.requests == []


def test_carousel_rejects_local_or_non_https_media() -> None:
    transport = FakeTransport([])
    service = SocialGrowthService(
        MetaGraphClient(make_settings(), transport),
        InMemoryIdempotencyStore(),
    )

    with pytest.raises(ValueError, match="HTTPS"):
        service.publish_carousel(
            ["file:///tmp/slide-1.png", "http://localhost/slide-2.png"],
            "Açıklama",
        )

    assert transport.requests == []


def test_carousel_success_requires_meta_ids_at_every_gate() -> None:
    transport = FakeTransport(
        [
            GraphResponse(200, {"id": "child-1"}),
            GraphResponse(200, {"id": "child-2"}),
            GraphResponse(200, {"id": "carousel-container"}),
            GraphResponse(200, {"status_code": "FINISHED"}),
            GraphResponse(200, {"id": "published-media-id"}),
        ]
    )
    service = SocialGrowthService(
        MetaGraphClient(make_settings(), transport),
        InMemoryIdempotencyStore(),
    )

    evidence = service.publish_carousel(
        [
            "https://cdn.example.com/slide-1.png",
            "https://cdn.example.com/slide-2.png",
        ],
        "Açıklama",
    )

    assert evidence.status is OperationStatus.SUCCEEDED
    assert evidence.provider_id == "published-media-id"
    assert [request["data"].get("media_type") for request in transport.requests[:3]] == [
        None,
        None,
        "CAROUSEL",
    ]
    assert transport.requests[-1]["url"].endswith("/media_publish")


def test_missing_meta_id_fails_instead_of_reporting_success() -> None:
    transport = FakeTransport([GraphResponse(200, {})])
    service = SocialGrowthService(
        MetaGraphClient(make_settings(), transport),
        InMemoryIdempotencyStore(),
    )

    with pytest.raises(GraphAPIError, match="id"):
        service.publish_carousel(
            [
                "https://cdn.example.com/slide-1.png",
                "https://cdn.example.com/slide-2.png",
            ],
            "Açıklama",
        )


def test_comment_private_reply_is_idempotent_and_trigger_bound() -> None:
    transport = FakeTransport([GraphResponse(200, {"id": "private-reply-id"})])
    service = SocialGrowthService(
        MetaGraphClient(make_settings(), transport),
        InMemoryIdempotencyStore(),
        trigger_links={"PROMPT": "https://example.com/prompt-rehberi"},
    )
    event = CommentEvent("comment-123", "PROMPT lütfen", "example_user")

    first = service.handle_comment(event)
    second = service.handle_comment(event)
    ignored = service.handle_comment(CommentEvent("comment-456", "Merhaba", "other_user"))

    assert first.status is OperationStatus.SUCCEEDED
    assert first.provider_id == "private-reply-id"
    assert second.status is OperationStatus.DUPLICATE
    assert ignored.status is OperationStatus.IGNORED
    assert len(transport.requests) == 1
    assert transport.requests[0]["url"].endswith("/comment-123/private_replies")


def test_redis_idempotency_claim_is_atomic_and_releasable() -> None:
    store = RedisIdempotencyStore(FakeRedis())

    assert store.claim("comment-123") is True
    assert store.claim("comment-123") is False
    store.release("comment-123")
    assert store.claim("comment-123") is True


def test_redis_webhook_rate_limiter_rejects_excess_requests() -> None:
    limiter = RedisWebhookRateLimiter(FakeRedis(), requests_per_minute=2)

    assert limiter.allow("meta-source") is True
    assert limiter.allow("meta-source") is True
    assert limiter.allow("meta-source") is False


def test_dry_run_is_persisted_as_episode_and_action_record(tmp_path: Path) -> None:
    evidence_path = tmp_path / "episode_evidence.jsonl"
    service = SocialGrowthService(
        MetaGraphClient(make_settings(), FakeTransport([])),
        InMemoryIdempotencyStore(),
        evidence_sink=EpisodeEvidenceSink(evidence_path),
    )

    evidence = service.plan_carousel(
        [
            "https://cdn.example.com/slide-1.png",
            "https://cdn.example.com/slide-2.png",
        ],
        "Açıklama",
    )
    episode = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert evidence.status is OperationStatus.DRY_RUN
    assert episode["actions"][0]["step_id"] == "carousel_publish"
    assert episode["actions"][0]["success"] is False
    assert episode["verification"]["result_status"] is False


def test_webhook_router_blocks_live_action_by_default() -> None:
    settings = make_settings()
    transport = FakeTransport([])
    service = SocialGrowthService(
        MetaGraphClient(settings, transport),
        InMemoryIdempotencyStore(),
        trigger_links={"PROMPT": "https://example.com/prompt-rehberi"},
    )
    app = FastAPI()
    app.include_router(build_meta_webhook_router(settings, service), prefix="/meta")
    client = TestClient(app)
    body = json.dumps(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "field": "comments",
                            "value": {"id": "comment-123", "text": "PROMPT"},
                        }
                    ]
                }
            ]
        },
        separators=(",", ":"),
    ).encode()
    signature = "sha256=" + hmac.new(
        TEST_APP_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    challenge = client.get(
        "/meta/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-token-value",
            "hub.challenge": "challenge-123",
        },
    )
    response = client.post(
        "/meta/webhook",
        content=body,
        headers={"X-Hub-Signature-256": signature},
    )

    assert challenge.status_code == 200
    assert challenge.text == "challenge-123"
    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "BLOCKED"
    assert transport.requests == []


def test_standalone_app_requires_redis_and_keeps_live_actions_disabled() -> None:
    env = {
        "INSTAGRAM_ACCOUNT_ID": "17841400000000000",
        "INSTAGRAM_ACCESS_TOKEN": TEST_ACCESS_TOKEN,
        "META_APP_SECRET": TEST_APP_SECRET,
        "META_WEBHOOK_VERIFY_TOKEN": "verify-token-value",
        "META_API_VERSION": "v23.0",
        "SOCIAL_GROWTH_PLANNER_API_KEY": "planner-api-key-value-at-least-32-characters",
        "SOCIAL_GROWTH_TRIGGER_LINKS_JSON": json.dumps(
            {"PROMPT": "https://example.com/prompt-rehberi"}
        ),
    }
    with pytest.raises(ConfigurationError, match="SOCIAL_GROWTH_REDIS_URL"):
        create_app(env)

    env["SOCIAL_GROWTH_REDIS_URL"] = "redis://localhost:6379/15"
    missing_planner_key = dict(env)
    del missing_planner_key["SOCIAL_GROWTH_PLANNER_API_KEY"]
    with pytest.raises(ConfigurationError, match="SOCIAL_GROWTH_PLANNER_API_KEY"):
        create_app(missing_planner_key)

    env["GEMINI_API_KEY"] = "test-gemini-provider-key"
    env["MINIMAX_API_KEY"] = "test-minimax-provider-key"
    client = TestClient(create_app(env))
    health = client.get("/health")

    assert health.status_code == 200
    assert health.json()["live_actions_enabled"] is False
    assert health.json()["configured_video_providers"] == ["hailuo", "veo"]
    assert health.json()["video_provider_execution_enabled"] is False


def test_legacy_automation_never_claims_or_performs_live_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from workspace.carousel_engine import (
        competitor_auto_commenter,
        dm_automation_responder,
        run_e2e_system_test,
    )
    from workspace.carousel_engine.hardened_publisher import (
        PostVerificationError,
        publish_with_zero_trust,
    )

    monkeypatch.setattr(
        dm_automation_responder,
        "DM_LOG_FILE",
        tmp_path / "dm_log.json",
    )
    monkeypatch.setattr(
        competitor_auto_commenter,
        "COMPETITOR_LOG_FILE",
        tmp_path / "competitor_log.json",
    )
    monkeypatch.setattr(
        run_e2e_system_test,
        "BASE_DIR",
        tmp_path,
    )

    assert dm_automation_responder.process_incoming_comment_triggers() == []
    planned_replies = dm_automation_responder.process_incoming_comment_triggers(
        [{"username": "example", "comment": "PROMPT lütfen"}]
    )
    competitor_results = competitor_auto_commenter.auto_comment_on_competitor_posts()
    master_report = run_e2e_system_test.run_master_11_system_test()

    assert planned_replies[0]["status"] == "DRY_RUN"
    assert all(item["status"] == "BLOCKED_POLICY" for item in competitor_results)
    assert master_report["overall_status"] == "BLOCKED_UNVERIFIED"
    assert master_report["verified_passed_subsystems"] == 0
    with pytest.raises(PostVerificationError):
        publish_with_zero_trust()


def test_legacy_scripts_do_not_contain_plaintext_password_defaults() -> None:
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "workspace" / "carousel_engine" / "direct_instagram_poster.py",
        root / "workspace" / "carousel_engine" / "login_and_post.py",
        root / "workspace" / "carousel_engine" / "ensure_login.py",
        root / "workspace" / "carousel_engine" / "login_now.py",
        root / "workspace" / "carousel_engine" / "playwright_instagram_poster.py",
        root / "workspace" / "carousel_engine" / "post_via_profile.py",
    ]

    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        password_lines = [
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith("PASSWORD")
        ]
        assert password_lines, f"{file_path.name} password ayarını açıkça yönetmeli"
        for line in password_lines:
            assert "os.environ[" in line or "os.getenv(" in line
            assert line.count('"') <= 2, f"{file_path.name} plaintext password içeriyor"
