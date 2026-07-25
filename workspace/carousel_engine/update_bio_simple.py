"""Deprecated compatibility entrypoint for simple bio UI editing."""

from workspace.carousel_engine.legacy_browser_guard import (
    block_legacy_browser_mutation,
)


def update_simple_bio() -> None:
    """Block browser-driven bio edits."""

    block_legacy_browser_mutation("Simple Instagram bio update")


if __name__ == "__main__":
    update_simple_bio()
