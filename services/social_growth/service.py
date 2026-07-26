"""Policy-aware social growth application service."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from services.social_growth.contracts import OperationEvidence, OperationStatus
from services.social_growth.meta_client import GraphAPIError, MetaGraphClient

MIN_CAROUSEL_ITEMS = 2
MAX_CAROUSEL_ITEMS = 10
MAX_CAPTION_LENGTH = 2_200
MAX_PRIVATE_REPLY_LENGTH = 1_000


@dataclass(frozen=True)
class CommentEvent:
    """Minimal normalized comment event."""

    comment_id: str
    text: str
    username: str | None = None


class IdempotencyStore(Protocol):
    """Prevents duplicate external actions for retried webhooks."""

    def claim(self, key: str) -> bool:
        """Atomically claim a key; false means it was already claimed."""

    def release(self, key: str) -> None:
        """Release a failed claim so a provider failure can be retried."""


class EvidenceSink(Protocol):
    """Persists governed operation evidence."""

    def record(self, evidence: OperationEvidence) -> None:
        """Persist one evidence record."""


class InMemoryIdempotencyStore:
    """Process-local store for tests; production should use a durable atomic store."""

    def __init__(self) -> None:
        self._claimed: set[str] = set()

    def claim(self, key: str) -> bool:
        if key in self._claimed:
            return False
        self._claimed.add(key)
        return True

    def release(self, key: str) -> None:
        self._claimed.discard(key)


class RedisClient(Protocol):
    """Subset of redis-py used for atomic idempotency claims."""

    def set(
        self,
        name: str,
        value: str,
        *,
        nx: bool,
        ex: int,
    ) -> object:
        """Set a key only when absent."""

    def delete(self, *names: str) -> int:
        """Delete one or more keys."""


class RedisIdempotencyStore:
    """Durable, cross-process idempotency backed by Redis SET NX."""

    def __init__(
        self,
        client: RedisClient,
        *,
        key_prefix: str = "social-growth:idempotency:",
        ttl_seconds: int = 8 * 24 * 60 * 60,
    ) -> None:
        if ttl_seconds < 60:
            raise ValueError("Idempotency TTL en az 60 saniye olmalı")
        self._client = client
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    def claim(self, key: str) -> bool:
        claimed = self._client.set(
            f"{self._key_prefix}{key}",
            "1",
            nx=True,
            ex=self._ttl_seconds,
        )
        return bool(claimed)

    def release(self, key: str) -> None:
        self._client.delete(f"{self._key_prefix}{key}")


class SocialGrowthService:
    """Coordinates validation, idempotency, provider calls, and evidence."""

    def __init__(
        self,
        client: MetaGraphClient,
        idempotency_store: IdempotencyStore,
        trigger_links: dict[str, str] | None = None,
        evidence_sink: EvidenceSink | None = None,
    ) -> None:
        self.client = client
        self.idempotency_store = idempotency_store
        self.evidence_sink = evidence_sink
        self.trigger_links = {
            key.upper(): value for key, value in (trigger_links or {}).items()
        }

    def publish_carousel(self, media_urls: list[str], caption: str) -> OperationEvidence:
        """Publish a validated carousel and return provider-backed evidence."""

        self._validate_carousel(media_urls, caption)
        child_ids = [self.client.create_carousel_item(url) for url in media_urls]
        container_id = self.client.create_carousel(child_ids, caption)
        status = self.client.get_container_status(container_id)
        if status != "FINISHED":
            raise GraphAPIError(f"Carousel container publish için hazır değil: {status}")
        media_id = self.client.publish_container(container_id)
        return self._record(
            OperationEvidence(
                operation="carousel_publish",
                status=OperationStatus.SUCCEEDED,
                provider_id=media_id,
                metadata={
                    "container_id": container_id,
                    "item_count": len(media_urls),
                },
            )
        )

    def plan_carousel(self, media_urls: list[str], caption: str) -> OperationEvidence:
        """Validate a carousel without performing any external action."""

        self._validate_carousel(media_urls, caption)
        return self._record(
            OperationEvidence(
                operation="carousel_publish",
                status=OperationStatus.DRY_RUN,
                reason="Dış etki insan onayı ve geçerli Meta credentials bekliyor",
                metadata={"item_count": len(media_urls)},
            )
        )

    def handle_comment(self, event: CommentEvent) -> OperationEvidence:
        """Reply once when a configured keyword is present in a verified comment."""

        trigger = self._match_trigger(event.text)
        if trigger is None:
            return self._record(
                OperationEvidence(
                    operation="comment_private_reply",
                    status=OperationStatus.IGNORED,
                    reason="Eşleşen izinli tetikleyici yok",
                )
            )

        claim_key = f"instagram-comment:{event.comment_id}"
        if not self.idempotency_store.claim(claim_key):
            return self._record(
                OperationEvidence(
                    operation="comment_private_reply",
                    status=OperationStatus.DUPLICATE,
                    reason="Comment daha önce işlendi",
                )
            )

        message = f"{trigger} rehberi: {self.trigger_links[trigger]}"
        if len(message) > MAX_PRIVATE_REPLY_LENGTH:
            self.idempotency_store.release(claim_key)
            raise ValueError("Private reply mesajı izin verilen sınırı aşıyor")
        try:
            provider_id = self.client.send_private_reply(event.comment_id, message)
        except Exception:
            self.idempotency_store.release(claim_key)
            raise
        return self._record(
            OperationEvidence(
                operation="comment_private_reply",
                status=OperationStatus.SUCCEEDED,
                provider_id=provider_id,
                metadata={"comment_id": event.comment_id, "trigger": trigger},
            )
        )

    def _record(self, evidence: OperationEvidence) -> OperationEvidence:
        if self.evidence_sink is not None:
            self.evidence_sink.record(evidence)
        return evidence

    def _match_trigger(self, text: str) -> str | None:
        for trigger in self.trigger_links:
            if re.search(rf"(?<!\w){re.escape(trigger)}(?!\w)", text, re.IGNORECASE):
                return trigger
        return None

    @staticmethod
    def _validate_carousel(media_urls: list[str], caption: str) -> None:
        if not MIN_CAROUSEL_ITEMS <= len(media_urls) <= MAX_CAROUSEL_ITEMS:
            raise ValueError("Carousel 2 ile 10 medya öğesi içermeli")
        if len(caption) > MAX_CAPTION_LENGTH:
            raise ValueError("Caption 2200 karakter sınırını aşıyor")
        for media_url in media_urls:
            SocialGrowthService._validate_public_https_url(media_url)

    @staticmethod
    def _validate_public_https_url(media_url: str) -> None:
        parsed = urlparse(media_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("Her carousel medyası public HTTPS URL olmalı")
        if parsed.username or parsed.password:
            raise ValueError("Medya URL'si credential içeremez")
        host = parsed.hostname.lower()
        if host == "localhost" or host.endswith(".localhost"):
            raise ValueError("Her carousel medyası public HTTPS URL olmalı")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return
        if not address.is_global:
            raise ValueError("Her carousel medyası public HTTPS URL olmalı")
