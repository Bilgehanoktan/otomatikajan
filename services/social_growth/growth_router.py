"""Authenticated HTTP contract for deterministic account growth plans."""

from __future__ import annotations

import hmac
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from services.social_growth.growth_plan import AccountGrowthPlanBuilder

MIN_API_KEY_LENGTH = 32


class GrowthPlanRateLimiter(Protocol):
    def allow(self, client_key: str) -> bool:
        """Return whether another growth plan may be created."""


class GrowthPlanRequest(BaseModel):
    handle: str = Field(min_length=1, max_length=31)


def build_growth_plan_router(
    builder: AccountGrowthPlanBuilder,
    *,
    api_key: str,
    rate_limiter: GrowthPlanRateLimiter | None = None,
) -> APIRouter:
    if len(api_key) < MIN_API_KEY_LENGTH:
        raise ValueError(f"api_key en az {MIN_API_KEY_LENGTH} karakter olmalı")
    router = APIRouter(tags=["account-growth-plan"])

    @router.post("/account-growth/plans", status_code=status.HTTP_201_CREATED)
    async def create_growth_plan(
        payload: GrowthPlanRequest,
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
            return builder.build(payload.handle).to_dict()
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_ACCOUNT_GROWTH_PLAN", "message": str(exc)},
            ) from exc

    return router
