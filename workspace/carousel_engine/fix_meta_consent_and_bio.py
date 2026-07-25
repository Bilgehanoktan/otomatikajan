"""Deprecated compatibility entrypoint for consent and bio UI mutation."""

from workspace.carousel_engine.legacy_browser_guard import (
    block_legacy_browser_mutation,
)


def fix_bio_update() -> None:
    """Block UI mutation of Meta consent or profile state."""

    block_legacy_browser_mutation("Meta consent and bio update")


if __name__ == "__main__":
    fix_bio_update()
