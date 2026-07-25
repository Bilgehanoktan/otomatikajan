"""Deprecated compatibility entrypoint for the unofficial Instagram publisher."""

from __future__ import annotations

import os

USERNAME = os.getenv("INSTAGRAM_USERNAME", "ai_gucum")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")


class LegacyInstagramLoginDisabledError(RuntimeError):
    """Raised because password-based Instagram automation is not production-safe."""


def get_instagram_client() -> None:
    """Block unofficial password/session login and direct callers to the Meta client."""

    raise LegacyInstagramLoginDisabledError(
        "Unverified instagrapi login disabled; use services.social_growth.MetaGraphClient"
    )


def publish_next_pending_carousel() -> None:
    """Block legacy publishing; provider-backed Meta Graph evidence is required."""

    raise LegacyInstagramLoginDisabledError(
        "Legacy publisher disabled; use SocialGrowthService.publish_carousel after approval"
    )


if __name__ == "__main__":
    publish_next_pending_carousel()
