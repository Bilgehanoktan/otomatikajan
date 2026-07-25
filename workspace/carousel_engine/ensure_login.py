"""Deprecated compatibility entrypoint for persistent browser login."""

from __future__ import annotations

import os

USERNAME = os.getenv("INSTAGRAM_USERNAME", "Ai_gucum_")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")


class LegacyInstagramLoginDisabledError(RuntimeError):
    """Raised because persistent cookie/session login is disabled."""


def ensure_login() -> None:
    """Block browser-profile authentication in favor of official Meta tokens."""

    raise LegacyInstagramLoginDisabledError(
        "Persistent browser login disabled; configure services.social_growth.MetaSettings"
    )


if __name__ == "__main__":
    ensure_login()
