"""Deprecated compatibility entrypoint for browser verification-code resend."""

from workspace.carousel_engine.legacy_browser_guard import (
    block_legacy_browser_mutation,
)


def resend_code() -> None:
    """Block browser/session account verification mutations."""

    block_legacy_browser_mutation("Instagram verification-code resend")


if __name__ == "__main__":
    resend_code()
