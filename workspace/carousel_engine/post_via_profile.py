"""Deprecated compatibility entrypoint for profile-page carousel uploads."""

from __future__ import annotations

import os

USERNAME = os.getenv("INSTAGRAM_USERNAME", "Ai_gucum_")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")


class LegacyInstagramLoginDisabledError(RuntimeError):
    """Raised because profile-page UI publishing is disabled."""


def publish_all_pending_carousels() -> None:
    """Block legacy batch publishing until the official provider gate is used."""

    raise LegacyInstagramLoginDisabledError(
        "Profile publisher disabled; use SocialGrowthService with human approval"
    )


if __name__ == "__main__":
    publish_all_pending_carousels()
