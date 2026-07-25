"""Deprecated compatibility entrypoint for interactive Instagram login."""

from workspace.carousel_engine.legacy_browser_guard import (
    block_legacy_browser_mutation,
)


def open_interactive_browser() -> None:
    """Block creation or refresh of a persistent Instagram browser session."""

    block_legacy_browser_mutation("Interactive Instagram login")


if __name__ == "__main__":
    open_interactive_browser()
