from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.auth.jwt_auth import require_permission
from services.integrations.free_web_api_catalog import (
    FreeWebApiProvider,
    available_categories,
    count_limited_free_providers,
    get_free_web_api_provider,
    list_free_web_api_providers,
)

router = APIRouter(tags=["Free Web API Catalog"])
require_free_web_api_view = require_permission("governor.view")


class FreeWebApiCatalogResponse(BaseModel):
    status: str
    strict_kotasiz: bool
    count: int
    excluded_limited_count: int
    categories: list[str]
    items: list[FreeWebApiProvider]


class FreeWebApiProviderResponse(BaseModel):
    status: str
    provider: FreeWebApiProvider


@router.get("/catalog", response_model=FreeWebApiCatalogResponse)
@router.get("/catalog/", response_model=FreeWebApiCatalogResponse)
async def get_free_web_api_catalog(
    strict_kotasiz: bool = Query(
        True,
        description="True olduğunda daily/monthly quota veya açık free-tier limiti olan adayları dışarıda bırakır.",
    ),
    category: str | None = Query(None, description="Opsiyonel kategori filtresi."),
    include_limited: bool = Query(
        False,
        description="strict_kotasiz=false iken sınırlı free-tier adayları da döndürür.",
    ),
    _identity: dict = Depends(require_free_web_api_view),
) -> FreeWebApiCatalogResponse:
    providers = list_free_web_api_providers(
        strict_kotasiz=strict_kotasiz,
        category=category,
        include_limited=include_limited,
    )
    return FreeWebApiCatalogResponse(
        status="success",
        strict_kotasiz=strict_kotasiz,
        count=len(providers),
        excluded_limited_count=count_limited_free_providers(),
        categories=available_categories(),
        items=providers,
    )


@router.get("/providers/{provider_id}", response_model=FreeWebApiProviderResponse)
@router.get("/providers/{provider_id}/", response_model=FreeWebApiProviderResponse)
async def get_free_web_api_provider_detail(
    provider_id: str,
    _identity: dict = Depends(require_free_web_api_view),
) -> FreeWebApiProviderResponse:
    try:
        provider = get_free_web_api_provider(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="API provider kaydı bulunamadı.") from exc

    return FreeWebApiProviderResponse(status="success", provider=provider)
