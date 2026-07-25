"""Deprecated compatibility entrypoint for Playwright publishing."""

from __future__ import annotations

import os

USERNAME = os.getenv("INSTAGRAM_USERNAME", "ai_gucum")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")


class LegacyInstagramLoginDisabledError(RuntimeError):
    """Raised because UI automation cannot produce trusted provider evidence."""


def handle_instagram_popups(page: object) -> None:
    """Reject calls that depend on an authenticated browser session."""

    del page
    raise LegacyInstagramLoginDisabledError(
        "Persistent browser automation disabled; use Meta webhook and Graph API"
    )


def publish_via_playwright() -> None:
    """Block browser publishing in favor of SocialGrowthService."""

    raise LegacyInstagramLoginDisabledError(
        "Playwright publisher disabled; use SocialGrowthService.publish_carousel"
    )


if __name__ == "__main__":
    publish_via_playwright()
