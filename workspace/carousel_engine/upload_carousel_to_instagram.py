"""Deprecated compatibility entrypoint for carousel UI upload."""

from workspace.carousel_engine.legacy_browser_guard import (
    block_legacy_browser_mutation,
)


def upload_next_carousel() -> None:
    """Block UI upload; official Graph provider evidence is required."""

    block_legacy_browser_mutation("Carousel UI upload")


if __name__ == "__main__":
    upload_next_carousel()
