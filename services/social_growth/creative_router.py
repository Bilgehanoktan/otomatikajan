"""Authenticated HTTP contract for grounded GPT creative packages."""

from __future__ import annotations

import hmac
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Request, status
from starlette.concurrency import run_in_threadpool

from services.social_growth.content_orchestrator import (
    DuplicateKeywordError,
    ProviderRoutingError,
    UngroundedClaimError,
)
from services.social_growth.content_router import ContentPlanRateLimiter, ContentPlanRequest
from services.social_growth.creative_planner import (
    CreativePlanningError,
    CreativeProductionPackage,
    UngroundedCreativeDraftError,
)

MIN_API_KEY_LENGTH = 32


class CreativeAgent(Protocol):
    def prepare(self, brief: Any) -> CreativeProductionPackage:
        """Prepare a grounded creative package."""


def build_creative_agent_router(
    agent: CreativeAgent | None,
    *,
    api_key: str,
    rate_limiter: ContentPlanRateLimiter | None = None,
) -> APIRouter:
    if len(api_key) < MIN_API_KEY_LENGTH:
        raise ValueError(f"api_key en az {MIN_API_KEY_LENGTH} karakter olmalı")
    router = APIRouter(tags=["creative-production-agent"])

    @router.post("/content/creative-packages", status_code=status.HTTP_201_CREATED)
    async def create_creative_package(
        payload: ContentPlanRequest,
        request: Request,
        planner_key: str | None = Header(
            default=None,
            alias="X-Content-Orchestrator-Key",
        ),
    ) -> dict[str, Any]:
        supplied_key = planner_key or ""
        if not hmac.compare_digest(supplied_key.encode(), api_key.encode()):
            raise HTTPException(
                status_code=401,
                detail={"code": "CONTENT_PLANNER_AUTH_REQUIRED"},
            )
        client_key = request.client.host if request.client else "unknown"
        if rate_limiter is not None and not rate_limiter.allow(client_key):
            raise HTTPException(
                status_code=429,
                detail={"code": "CONTENT_PLANNER_RATE_LIMITED"},
            )
        if agent is None:
            raise HTTPException(
                status_code=503,
                detail={"code": "CREATIVE_PLANNER_NOT_CONFIGURED"},
            )
        try:
            package = await run_in_threadpool(agent.prepare, payload.to_domain())
            return package.to_dict()
        except (UngroundedClaimError, UngroundedCreativeDraftError) as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "BLOCKED_UNGROUNDED_CREATIVE", "message": str(exc)},
            ) from exc
        except DuplicateKeywordError as exc:
            raise HTTPException(
                status_code=409,
                detail={"code": "DUPLICATE_CTA_KEYWORD", "message": str(exc)},
            ) from exc
        except ProviderRoutingError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "BLOCKED_PROVIDER_ROUTE", "message": str(exc)},
            ) from exc
        except CreativePlanningError as exc:
            raise HTTPException(
                status_code=502,
                detail={"code": "CREATIVE_PLANNER_FAILED", "message": str(exc)},
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_CONTENT_BRIEF", "message": str(exc)},
            ) from exc

    return router
