"""Deprecated compatibility entrypoint for the browser publisher."""

from workspace.carousel_engine.legacy_browser_guard import (
    LegacyBrowserMutationDisabledError,
    block_legacy_browser_mutation,
)

PostVerificationError = LegacyBrowserMutationDisabledError


def publish_with_zero_trust() -> None:
    """Block the legacy publisher whose DOM checks were not provider evidence."""

    block_legacy_browser_mutation("Legacy zero-trust browser publisher")


if __name__ == "__main__":
    publish_with_zero_trust()
