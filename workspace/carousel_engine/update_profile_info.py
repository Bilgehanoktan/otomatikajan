"""Deprecated compatibility entrypoint for browser profile mutation."""

from workspace.carousel_engine.legacy_browser_guard import (
    block_legacy_browser_mutation,
)


def update_instagram_profile_info() -> None:
    """Block UI-driven Instagram profile edits."""

    block_legacy_browser_mutation("Instagram profile update")


if __name__ == "__main__":
    update_instagram_profile_info()
