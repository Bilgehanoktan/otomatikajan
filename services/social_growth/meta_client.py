"""Small, injectable client for the official Meta Graph API surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote

import httpx

from services.social_growth.config import MetaSettings

REQUEST_TIMEOUT_SECONDS = 20.0
RECENT_MEDIA_FIELDS = (
    "id,caption,media_type,permalink,timestamp,comments_count"
)


class GraphAPIError(RuntimeError):
    """Raised for transport errors or malformed Meta Graph responses."""


@dataclass(frozen=True)
class GraphResponse:
    """Transport-neutral Graph response."""

    status_code: int
    payload: dict[str, Any]


class GraphTransport(Protocol):
    """Injectable transport contract used by tests and production."""

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> GraphResponse:
        """Send one Graph request and return parsed JSON."""


class HttpxGraphTransport:
    """Synchronous HTTP transport with bounded timeouts."""

    def __init__(self, timeout: float = REQUEST_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> GraphResponse:
        """Execute a request without logging headers or request bodies."""

        try:
            response = httpx.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                timeout=self._timeout,
                follow_redirects=False,
            )
        except httpx.HTTPError as exc:
            raise GraphAPIError(f"Meta Graph transport hatası: {type(exc).__name__}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise GraphAPIError("Meta Graph JSON olmayan bir response döndürdü") from exc
        if not isinstance(payload, dict):
            raise GraphAPIError("Meta Graph response nesne biçiminde değil")
        return GraphResponse(response.status_code, payload)


class MetaGraphClient:
    """Official Graph calls needed by the social growth service."""

    def __init__(self, settings: MetaSettings, transport: GraphTransport | None = None) -> None:
        self.settings = settings
        self.transport = transport or HttpxGraphTransport()

    def create_carousel_item(self, image_url: str) -> str:
        """Create one image container for a future carousel."""

        payload = self._post(
            self.settings.account_id,
            "media",
            data={"image_url": image_url, "is_carousel_item": "true"},
        )
        return self._required_id(payload, "carousel child")

    def create_carousel(self, child_ids: list[str], caption: str) -> str:
        """Create a carousel parent container."""

        payload = self._post(
            self.settings.account_id,
            "media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(child_ids),
                "caption": caption,
            },
        )
        return self._required_id(payload, "carousel container")

    def get_container_status(self, container_id: str) -> str:
        """Read the provider processing status for a creation container."""

        payload = self._get(container_id, params={"fields": "status_code"})
        status = payload.get("status_code")
        if not isinstance(status, str) or not status:
            raise GraphAPIError("Meta Graph response içinde status_code yok")
        return status

    def publish_container(self, container_id: str) -> str:
        """Publish a finished creation container."""

        payload = self._post(
            self.settings.account_id,
            "media_publish",
            data={"creation_id": container_id},
        )
        return self._required_id(payload, "published media")

    def send_private_reply(self, comment_id: str, message: str) -> str:
        """Send the single allowed private reply tied to a comment ID."""

        payload = self._post(comment_id, "private_replies", data={"message": message})
        for key in ("id", "message_id", "recipient_id"):
            provider_id = payload.get(key)
            if isinstance(provider_id, str) and provider_id:
                return provider_id
        raise GraphAPIError("Meta private reply response içinde provider id yok")

    def list_recent_media(self, limit: int = 10) -> list[dict[str, Any]]:
        """List a bounded set of owned media without following provider paging URLs."""

        if isinstance(limit, bool) or not 1 <= limit <= 25:
            raise ValueError("Media limiti 1 ile 25 arasında olmalı")
        payload = self._get(
            self.settings.account_id,
            "media",
            params={"fields": RECENT_MEDIA_FIELDS, "limit": limit},
        )
        data = payload.get("data")
        if not isinstance(data, list):
            raise GraphAPIError("Meta media response içinde geçerli data listesi yok")
        if any(not isinstance(item, dict) for item in data):
            raise GraphAPIError("Meta media data öğeleri nesne biçiminde olmalı")
        return [dict(item) for item in data[:limit]]

    def get_insights(self, metrics: list[str], period: str = "day") -> dict[str, Any]:
        """Read account insights without converting missing data into success."""

        if not metrics:
            raise ValueError("En az bir insight metriği gerekli")
        return self._get(
            self.settings.account_id,
            "insights",
            params={"metric": ",".join(metrics), "period": period},
        )

    def _get(
        self,
        *path_parts: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request("GET", *path_parts, params=params)

    def _post(
        self,
        *path_parts: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return self._request("POST", *path_parts, data=data)

    def _request(
        self,
        method: str,
        *path_parts: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = "/".join(quote(part, safe="") for part in path_parts)
        base = self.settings.graph_base_url.rstrip("/")
        url = f"{base}/{self.settings.api_version}/{path}"
        response = self.transport.request(
            method,
            url,
            params=params,
            data=data,
            headers={
                "Authorization": f"Bearer {self.settings.access_token}",
                "Accept": "application/json",
            },
        )
        if response.status_code < 200 or response.status_code >= 300:
            error = response.payload.get("error", {})
            code = error.get("code", "unknown") if isinstance(error, dict) else "unknown"
            raise GraphAPIError(
                f"Meta Graph isteği başarısız: HTTP {response.status_code}, code={code}"
            )
        return response.payload

    @staticmethod
    def _required_id(payload: dict[str, Any], operation: str) -> str:
        provider_id = payload.get("id")
        if not isinstance(provider_id, str) or not provider_id:
            raise GraphAPIError(f"Meta {operation} response içinde id yok")
        return provider_id
