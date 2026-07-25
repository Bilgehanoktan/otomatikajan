"""Deprecated compatibility entrypoint for browser bio editing."""

from workspace.carousel_engine.legacy_browser_guard import (
    block_legacy_browser_mutation,
)


def update_bio_clean() -> None:
    """Block browser-driven profile edits."""

    block_legacy_browser_mutation("Browser bio update")


if __name__ == "__main__":
    update_bio_clean()
