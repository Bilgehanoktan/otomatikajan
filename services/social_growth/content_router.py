"""FastAPI contract for side-effect-free ContentOrchestrator plans."""

from __future__ import annotations

import hmac
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from services.social_growth.content_orchestrator import (
    Claim,
    ContentBrief,
    ContentFormat,
    ContentMode,
    ContentOrchestrator,
    ContentTemplate,
    CTAMode,
    DuplicateKeywordError,
    ProviderRoutingError,
    ProviderRoutingMode,
    UngroundedClaimError,
    VideoProvider,
)

MIN_PLANNER_API_KEY_LENGTH = 32


class ContentPlanRateLimiter(Protocol):
    """Ingress limiter for authenticated planning requests."""

    def allow(self, client_key: str) -> bool:
        """Return whether the caller may create another plan."""


class ClaimRequest(BaseModel):
    """HTTP representation of a grounded or explicitly non-verifiable claim."""

    text: str = Field(min_length=1, max_length=1_000)
    source_urls: list[str] = Field(default_factory=list, max_length=10)
    verifiable: bool = True


class ContentPlanRequest(BaseModel):
    """Validated HTTP request before domain-level governance checks."""

    topic: str = Field(min_length=1, max_length=240)
    audience: str = Field(min_length=1, max_length=240)
    mode: ContentMode
    format: ContentFormat
    template: ContentTemplate
    cta_mode: CTAMode
    keyword: str | None = Field(default=None, max_length=24)
    routing_mode: ProviderRoutingMode = ProviderRoutingMode.AUTO
    preferred_providers: list[VideoProvider] = Field(default_factory=list, max_length=4)
    claims: list[ClaimRequest] = Field(default_factory=list, max_length=20)

    def to_domain(self) -> ContentBrief:
        return ContentBrief(
            topic=self.topic,
            audience=self.audience,
            mode=self.mode,
            format=self.format,
            template=self.template,
            cta_mode=self.cta_mode,
            keyword=self.keyword,
            routing_mode=self.routing_mode,
            preferred_providers=tuple(self.preferred_providers),
            claims=tuple(
                Claim(
                    text=claim.text,
                    source_urls=tuple(claim.source_urls),
                    verifiable=claim.verifiable,
                )
                for claim in self.claims
            ),
        )


def build_content_orchestrator_router(
    orchestrator: ContentOrchestrator,
    *,
    api_key: str,
    rate_limiter: ContentPlanRateLimiter | None = None,
) -> APIRouter:
    """Build a planner-only router with explicit fail-closed error codes."""

    if len(api_key) < MIN_PLANNER_API_KEY_LENGTH:
        raise ValueError(f"api_key en az {MIN_PLANNER_API_KEY_LENGTH} karakter olmalı")
    router = APIRouter(tags=["content-orchestrator"])

    @router.post("/content/plans", status_code=status.HTTP_201_CREATED)
    async def create_content_plan(
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
        try:
            plan = orchestrator.plan(payload.to_domain())
        except UngroundedClaimError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "BLOCKED_UNGROUNDED_CLAIM",
                    "message": str(exc),
                },
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
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_CONTENT_BRIEF", "message": str(exc)},
            ) from exc
        return plan.to_dict()

    return router
