"""Standalone FastAPI application factory for the social growth webhook."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI
from redis import Redis

from services.social_growth.audit import EpisodeEvidenceSink
from services.social_growth.config import ConfigurationError, MetaSettings
from services.social_growth.content_orchestrator import (
    ContentOrchestrator,
    RedisKeywordClient,
    RedisKeywordRegistry,
    VideoProvider,
)
from services.social_growth.content_router import build_content_orchestrator_router
from services.social_growth.creative_planner import (
    CreativeProductionAgent,
    build_openai_creative_planner,
)
from services.social_growth.creative_router import build_creative_agent_router
from services.social_growth.growth_plan import AccountGrowthPlanBuilder
from services.social_growth.growth_router import build_growth_plan_router
from services.social_growth.meta_client import MetaGraphClient
from services.social_growth.rate_limit import RateLimitRedisClient, RedisWebhookRateLimiter
from services.social_growth.router import build_meta_webhook_router
from services.social_growth.service import RedisClient, RedisIdempotencyStore, SocialGrowthService
from services.social_growth.video_providers import (
    HailuoVideoAdapter,
    ProviderExecutionRegistry,
    VeoVideoAdapter,
    VideoProviderAdapter,
)

APPROVAL_FLAG = "SOCIAL_GROWTH_LIVE_ACTIONS_APPROVED"
TRIGGER_LINKS_ENV = "SOCIAL_GROWTH_TRIGGER_LINKS_JSON"
REDIS_URL_ENV = "SOCIAL_GROWTH_REDIS_URL"
EVIDENCE_PATH_ENV = "SOCIAL_GROWTH_EVIDENCE_PATH"
PLANNER_API_KEY_ENV = "SOCIAL_GROWTH_PLANNER_API_KEY"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_MODEL_ENV = "SOCIAL_GROWTH_OPENAI_MODEL"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
MINIMAX_API_KEY_ENV = "MINIMAX_API_KEY"
PLANNER_REQUESTS_PER_MINUTE = 30


def create_app(env: Mapping[str, str] | None = None) -> FastAPI:
    """Build the app from validated settings without reading secrets at import time."""

    source = os.environ if env is None else env
    settings = MetaSettings.from_env(source)
    trigger_links = _load_trigger_links(source)
    redis_url = source.get(REDIS_URL_ENV, "")
    if not redis_url:
        raise ConfigurationError(f"{REDIS_URL_ENV} zorunludur")
    planner_api_key = source.get(PLANNER_API_KEY_ENV, "")
    if len(planner_api_key) < 32:
        raise ConfigurationError(f"{PLANNER_API_KEY_ENV} en az 32 karakter olmalı")

    redis_client = Redis.from_url(redis_url, decode_responses=True)
    store = RedisIdempotencyStore(cast(RedisClient, redis_client))
    evidence_sink = EpisodeEvidenceSink(
        Path(
            source.get(
                EVIDENCE_PATH_ENV,
                "runtime/social_growth/episode_evidence.jsonl",
            )
        )
    )
    service = SocialGrowthService(
        MetaGraphClient(settings),
        store,
        trigger_links=trigger_links,
        evidence_sink=evidence_sink,
    )
    live_actions_enabled = source.get(APPROVAL_FLAG, "").lower() == "true"
    content_orchestrator = ContentOrchestrator(
        keyword_registry=RedisKeywordRegistry(
            cast(RedisKeywordClient, redis_client)
        ),
        evidence_sink=evidence_sink,
    )
    openai_api_key = source.get(OPENAI_API_KEY_ENV, "")
    provider_adapters: dict[VideoProvider, VideoProviderAdapter] = {}
    gemini_api_key = source.get(GEMINI_API_KEY_ENV, "")
    if gemini_api_key:
        provider_adapters[VideoProvider.VEO] = VeoVideoAdapter(gemini_api_key)
    minimax_api_key = source.get(MINIMAX_API_KEY_ENV, "")
    if minimax_api_key:
        provider_adapters[VideoProvider.HAILUO] = HailuoVideoAdapter(minimax_api_key)
    provider_registry = ProviderExecutionRegistry(
        provider_adapters,
        evidence_sink=evidence_sink,
    )
    creative_agent = None
    if openai_api_key:
        creative_agent = CreativeProductionAgent(
            content_orchestrator,
            build_openai_creative_planner(
                openai_api_key,
                model=source.get(OPENAI_MODEL_ENV, "gpt-5.6-terra"),
            ),
            evidence_sink=evidence_sink,
            provider_registry=provider_registry,
        )

    app = FastAPI(title="AI Gücüm Social Growth Webhook", version="1.0.0")
    app.state.creative_agent = creative_agent
    app.state.video_provider_registry = provider_registry
    app.include_router(
        build_meta_webhook_router(
            settings,
            service,
            live_actions_enabled=live_actions_enabled,
            rate_limiter=RedisWebhookRateLimiter(
                cast(RateLimitRedisClient, redis_client)
            ),
        ),
        prefix="/api/v1/social-growth",
    )
    app.include_router(
        build_content_orchestrator_router(
            content_orchestrator,
            api_key=planner_api_key,
            rate_limiter=RedisWebhookRateLimiter(
                cast(RateLimitRedisClient, redis_client),
                requests_per_minute=PLANNER_REQUESTS_PER_MINUTE,
                key_prefix="social-growth:content-plan-rate:",
            ),
        ),
        prefix="/api/v1/social-growth",
    )
    app.include_router(
        build_creative_agent_router(
            creative_agent,
            api_key=planner_api_key,
            rate_limiter=RedisWebhookRateLimiter(
                cast(RateLimitRedisClient, redis_client),
                requests_per_minute=PLANNER_REQUESTS_PER_MINUTE,
                key_prefix="social-growth:creative-package-rate:",
            ),
        ),
        prefix="/api/v1/social-growth",
    )
    app.include_router(
        build_growth_plan_router(
            AccountGrowthPlanBuilder(evidence_sink=evidence_sink),
            api_key=planner_api_key,
            rate_limiter=RedisWebhookRateLimiter(
                cast(RateLimitRedisClient, redis_client),
                requests_per_minute=PLANNER_REQUESTS_PER_MINUTE,
                key_prefix="social-growth:growth-plan-rate:",
            ),
        ),
        prefix="/api/v1/social-growth",
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ready",
            "live_actions_enabled": live_actions_enabled,
            "creative_planner_enabled": creative_agent is not None,
            "video_provider_execution_enabled": False,
            "configured_video_providers": sorted(
                provider.value for provider in provider_adapters
            ),
            "provider": "meta_graph",
        }

    return app


def _load_trigger_links(source: Mapping[str, str]) -> dict[str, str]:
    raw = source.get(TRIGGER_LINKS_ENV, "")
    if not raw:
        raise ConfigurationError(f"{TRIGGER_LINKS_ENV} zorunludur")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"{TRIGGER_LINKS_ENV} geçerli JSON olmalı") from exc
    if not isinstance(payload, dict) or not payload:
        raise ConfigurationError(f"{TRIGGER_LINKS_ENV} boş olmayan bir nesne olmalı")

    links: dict[str, str] = {}
    for trigger, link in payload.items():
        if not isinstance(trigger, str) or not trigger.strip():
            raise ConfigurationError("Tetikleyici adları boş olmayan string olmalı")
        if not isinstance(link, str) or not link.startswith("https://"):
            raise ConfigurationError("Tetikleyici linkleri HTTPS olmalı")
        links[trigger.strip().upper()] = link
    return links
