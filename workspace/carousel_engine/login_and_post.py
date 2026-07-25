"""Deprecated compatibility entrypoint for browser-based Instagram publishing."""

from __future__ import annotations

import os

USERNAME = os.getenv("INSTAGRAM_USERNAME", "Ai_gucum_")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")


class LegacyInstagramLoginDisabledError(RuntimeError):
    """Raised because password/browser-profile automation is disabled."""


def run_login_and_post() -> None:
    """Block legacy login and require the official Meta Graph API service."""

    raise LegacyInstagramLoginDisabledError(
        "Browser login publisher disabled; use services.social_growth with human approval"
    )


if __name__ == "__main__":
    run_login_and_post()
