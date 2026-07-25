"""Deprecated compatibility entrypoint for immediate browser login."""

from __future__ import annotations

import os

USERNAME = os.getenv("INSTAGRAM_USERNAME", "Ai_gucum_")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")


class LegacyInstagramLoginDisabledError(RuntimeError):
    """Raised because password and persistent-session login is disabled."""


def login_now() -> None:
    """Block browser login and direct operators to official Meta authentication."""

    raise LegacyInstagramLoginDisabledError(
        "Browser login disabled; configure services.social_growth.MetaSettings"
    )


if __name__ == "__main__":
    login_now()
